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

import json
from oslo_log import log as logging
from testtools.matchers import HasLength

from vitrage import os_clients
from vitrage_tempest_plugin.tests.api.event.base import BaseTestEvents
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


class TestMistralNotifier(BaseTestEvents):

    TRIGGER_ALARM_1 = "notifiers.mistral.trigger.alarm.1"
    TRIGGER_ALARM_2 = "notifiers.mistral.trigger.alarm.2"
    TRIGGER_ALARM_FOR_FUNCTION = "notifiers.mistral.trigger.alarm.for.function"

    def setUp(self):
        super(TestMistralNotifier, self).setUp()

    def tearDown(self):
        super(TestMistralNotifier, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestMistralNotifier, cls).setUpClass()
        cls.mistral_client = os_clients.mistral_client(cls.conf)
        cls._templates = []
        cls._templates.append(v_utils.add_template('v1_execute_mistral.yaml'))
        cls._templates.append(v_utils.add_template('v2_execute_mistral.yaml'))

    @classmethod
    def tearDownClass(cls):
        if cls._templates is not None:
            v_utils.delete_template(cls._templates[0]['uuid'])
            v_utils.delete_template(cls._templates[1]['uuid'])

    @utils.tempest_logger
    def test_execute_mistral_v1(self):
        self._do_test_execute_mistral(self.TRIGGER_ALARM_1)

    @utils.tempest_logger
    def test_execute_mistral_v2(self):
        self._do_test_execute_mistral(self.TRIGGER_ALARM_2)

    @utils.tempest_logger
    def test_execute_mistral_with_function(self):
        # Execute the basic test
        self._do_test_execute_mistral(self.TRIGGER_ALARM_FOR_FUNCTION)

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

        execution_input = json.loads(execution_input_str)

        farewell_value = execution_input['farewell']
        self.assertIsNotNone(farewell_value, '\'farewell\' input parameter is '
                                             'None in last workflow execution')

        self.assertEqual(self.TRIGGER_ALARM_FOR_FUNCTION, farewell_value,
                         '\'farewell\' input parameter does not match the'
                         'alarm name')

    def _do_test_execute_mistral(self, trigger_alarm):
        workflows = self.mistral_client.workflows.list()
        self.assertIsNotNone(workflows, 'Failed to get the list of workflows')
        num_workflows = len(workflows)

        executions = self.mistral_client.executions.list()
        self.assertIsNotNone(executions,
                             'Failed to get the list of workflow executions')
        num_executions = len(executions)

        alarms = utils.wait_for_answer(2, 0.5, self._check_alarms)
        self.assertIsNotNone(alarms, 'Failed to get the list of alarms')
        num_alarms = len(alarms)

        try:
            # Create a Mistral workflow
            self.mistral_client.workflows.create(WF_DEFINITION)

            # Validate the workflow creation
            workflows = self.mistral_client.workflows.list()
            self.assertIsNotNone(workflows,
                                 'Failed to get the list of workflows')
            self.assertThat(workflows, HasLength(num_workflows + 1),
                            'Mistral workflow was not created')

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

        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._rollback_to_default(WF_NAME, num_workflows,
                                      trigger_alarm, num_alarms)
            pass

    def _rollback_to_default(self, workflow_name, num_workflows,
                             trigger_alarm, num_alarms):
        # Delete the workflow
        self.mistral_client.workflows.delete(workflow_name)

        workflows = self.mistral_client.workflows.list()
        self.assertIsNotNone(workflows, 'Failed to get the list of workflows')
        self.assertThat(workflows, HasLength(num_workflows),
                        'Failed to remove the test workflow')

        # Clear the trigger alarm and wait it to be deleted
        self._trigger_undo_action(trigger_alarm)

        self.assertTrue(wait_for_status(
            10,
            self._check_num_vitrage_alarms,
            num_alarms=num_alarms),
            'Vitrage trigger alarm was not deleted')

    @staticmethod
    def _check_num_vitrage_alarms(num_alarms):
        vitrage_alarms = TempestClients.vitrage().alarm.list(vitrage_id='all',
                                                             all_tenants=True)
        if len(vitrage_alarms) == num_alarms:
            return True
        return False

    def _check_mistral_workflow_execution(self, num_executions):
        if len(self.mistral_client.executions.list()) == num_executions:
            return True
        return False
