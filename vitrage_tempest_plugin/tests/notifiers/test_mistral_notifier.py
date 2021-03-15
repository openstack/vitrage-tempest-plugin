# Copyright 2017 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import time

from oslo_log import log as logging
from oslo_serialization import jsonutils
import testtools
from testtools.matchers import HasLength

from vitrage_tempest_plugin.tests.api.event.base import BaseTestEvents
from vitrage_tempest_plugin.tests.common import nova_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils
from vitrage_tempest_plugin.tests import utils
from vitrage_tempest_plugin.tests.utils import wait_for_status

LOG = logging.getLogger(__name__)


WF_NAME = 'wf_for_tempest_test_1234'

WF_DEFINITION = """
---
version: '2.0'

wf_for_tempest_test_1234:
  type: direct
  input:
    - farewell

  tasks:
    goodbye:
      action: std.echo output="<% $.farewell %>, Tempest Test!"
"""


@testtools.skip("skip for now until mistral fixes the failures")
class TestMistralNotifier(BaseTestEvents):

    TRIGGER_ALARM_1 = "notifiers.mistral.trigger.alarm.1"
    TRIGGER_ALARM_2 = "notifiers.mistral.trigger.alarm.2"
    TRIGGER_ALARM_3 = "notifiers.mistral.trigger.alarm.3"
    TRIGGER_ALARM_FOR_FUNCTION = "notifiers.mistral.trigger.alarm.for.function"
    TRIGGER_ALARM_FOR_FUNCTION_v3 = \
        "notifiers.mistral.trigger.alarm.for.function.v3"

    @classmethod
    def setUpClass(cls):
        super(TestMistralNotifier, cls).setUpClass()
        cls.mistral_client = TempestClients.mistral()
        cls._templates = []
        cls._templates.append(v_utils.add_template('v1_execute_mistral.yaml'))
        cls._templates.append(v_utils.add_template('v2_execute_mistral.yaml'))
        cls._templates.append(v_utils.add_template('v3_execute_mistral.yaml'))

        # Create a Mistral workflow
        cls.mistral_client.workflows.create(WF_DEFINITION)

    @classmethod
    def tearDownClass(cls):
        if cls._templates is not None:
            v_utils.delete_template(cls._templates[0]['uuid'])
            v_utils.delete_template(cls._templates[1]['uuid'])
            v_utils.delete_template(cls._templates[2]['uuid'])

        # Delete the workflow
        cls.mistral_client.workflows.delete(WF_NAME)
        nova_utils.delete_all_instances()

    @utils.tempest_logger
    def test_execute_mistral_v1(self):
        self._do_test_execute_mistral(self.TRIGGER_ALARM_1)

    @utils.tempest_logger
    def test_execute_mistral_v2(self):
        self._do_test_execute_mistral(self.TRIGGER_ALARM_2)

    @utils.tempest_logger
    def test_execute_mistral_v3(self):
        self._do_test_execute_mistral(self.TRIGGER_ALARM_3)

    @utils.tempest_logger
    def test_execute_mistral_with_function_v2(self):
        # Execute the basic test
        self._do_test_execute_mistral(self.TRIGGER_ALARM_FOR_FUNCTION)
        self._do_test_function(self.TRIGGER_ALARM_FOR_FUNCTION)

    @utils.tempest_logger
    def test_execute_mistral_with_function_v3(self):
        # Execute the basic test
        self._do_test_execute_mistral(self.TRIGGER_ALARM_FOR_FUNCTION_v3)
        self._do_test_function(self.TRIGGER_ALARM_FOR_FUNCTION_v3)

    @utils.tempest_logger
    def test_execute_mistral_more_than_once(self):
        executions = self.mistral_client.executions.list()
        self.assertIsNotNone(executions,
                             'Failed to get the list of workflow executions')
        num_executions = len(executions)

        # Make sure there are at least two instances in the environment
        nova_utils.create_instances(num_instances=2, set_public_network=True)
        num_instances = len(TempestClients.nova().servers.list())

        # Add a template that executes the same Mistral workflow for every
        # instance. This should immediately trigger execute_mistral actions.
        template = None
        try:
            template = v_utils.add_template('v3_execute_mistral_twice.yaml')
        finally:
            if template:
                v_utils.delete_template(template['uuid'])   # no longer needed

        time.sleep(2)   # wait for the evaluator to process the new template

        # Verify that there is an execution for every instance
        executions = self.mistral_client.executions.list()
        self.assertIsNotNone(executions,
                             'Failed to get the list of workflow executions')

        msg = "There are %d executions. Expected number of executions: %d " \
              "(old number of executions) + %d (number of instances)" % \
              (len(executions), num_executions, num_instances)
        self.assertThat(executions, HasLength(num_executions + num_instances),
                        msg)

        executed_on_instances = set()
        for i in range(num_instances):
            # There may be many old executions in the list. The relevant ones
            # are at the end. Check the last `num_instances` executions.
            execution = \
                self.mistral_client.executions.get(executions[-i].id)
            execution_input = jsonutils.loads(execution.input)
            executed_on_instances.add(execution_input['farewell'])

        msg = "There are %d instances in the graph but only %d distinct " \
              "executions" % (num_instances, len(executed_on_instances))
        self.assertThat(executed_on_instances, HasLength(num_instances), msg)

    def _do_test_function(self, trigger):
        # Make sure that the workflow execution was done with the correct input
        # (can be checked even if the Vitrage alarm is already down)
        executions = self.mistral_client.executions.list()
        last_execution = executions[0]
        for execution in executions:
            if execution.updated_at > last_execution.updated_at:
                last_execution = execution
        execution_input_str = last_execution.input
        self.assertIsNotNone(execution_input_str,
                             'The last execution had no input')
        self.assertIn('farewell', execution_input_str,
                      'No \'farewell\' key in the last execution input')
        execution_input = jsonutils.loads(execution_input_str)
        farewell_value = execution_input['farewell']
        self.assertIsNotNone(farewell_value, '\'farewell\' input parameter is '
                                             'None in last workflow execution')
        self.assertEqual(trigger, farewell_value,
                         '\'farewell\' input parameter does not match the'
                         'alarm name')

    def _do_test_execute_mistral(self, trigger_alarm):
        executions = self.mistral_client.executions.list()
        self.assertIsNotNone(executions,
                             'Failed to get the list of workflow executions')
        num_executions = len(executions)

        alarms = utils.wait_for_answer(2, 0.5, self._check_alarms)
        self.assertIsNotNone(alarms, 'Failed to get the list of alarms')
        num_alarms = len(alarms)

        try:
            # Trigger an alarm. According to v1_execute_mistral.yaml template,
            # the alarm should cause execution of the workflow
            self._trigger_do_action(trigger_alarm)

            # Wait for the alarm to be raised
            self.assertTrue(wait_for_status(
                10,
                self._check_num_vitrage_alarms,
                num_alarms=num_alarms + 1),
                'Trigger alarm was not raised')

            # Wait for the Mistral workflow execution
            self.assertTrue(wait_for_status(
                20,
                self._check_mistral_workflow_execution,
                num_executions=num_executions + 1),
                'Mistral workflow was not executed')

        finally:
            self._rollback_to_default(trigger_alarm, num_alarms)

    def _rollback_to_default(self, trigger_alarm, num_alarms):
        # Clear the trigger alarm and wait it to be deleted
        self._trigger_undo_action(trigger_alarm)

        self.assertTrue(wait_for_status(
            10,
            self._check_num_vitrage_alarms,
            num_alarms=num_alarms),
            'Vitrage trigger alarm was not deleted')

    @classmethod
    def _check_num_vitrage_alarms(cls, num_alarms):
        vitrage_alarms = cls.vitrage_client.alarm.list(vitrage_id='all',
                                                       all_tenants=True)
        if len(vitrage_alarms) == num_alarms:
            return True
        return False

    def _check_mistral_workflow_execution(self, num_executions):
        if len(self.mistral_client.executions.list()) == num_executions:
            return True
        return False
