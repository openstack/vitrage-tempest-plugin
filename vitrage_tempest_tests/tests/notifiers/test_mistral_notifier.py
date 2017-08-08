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

from oslo_log import log as logging
from testtools.matchers import HasLength

from vitrage import os_clients
from vitrage_tempest_tests.tests.api.event.base import BaseTestEvents
from vitrage_tempest_tests.tests.api.event.base import DOWN
from vitrage_tempest_tests.tests.api.event.base import UP
from vitrage_tempest_tests.tests import utils
from vitrage_tempest_tests.tests.utils import wait_for_answer

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

    @classmethod
    def setUpClass(cls):
        super(TestMistralNotifier, cls).setUpClass()
        cls.mistral_client = os_clients.mistral_client(cls.conf)

    @utils.tempest_logger
    def test_execute_mistral(self):
        hostname = self._get_host()['name']

        workflows = self.mistral_client.workflows.list()
        self.assertIsNotNone(workflows)
        num_workflows = len(workflows)

        executions = self.mistral_client.executions.list()
        self.assertIsNotNone(executions)
        num_executions = len(executions)

        alarms = wait_for_answer(2, 0.5, self._check_alarms)
        self.assertIsNotNone(alarms)
        num_alarms = len(alarms)

        try:
            # Create a Mistral workflow
            self.mistral_client.workflows.create(WF_DEFINITION)

            # Validate the workflow creation
            workflows = self.mistral_client.workflows.list()
            self.assertIsNotNone(workflows)
            self.assertThat(workflows, HasLength(num_workflows + 1))

            # Send a Doctor event that should generate an alarm. According to
            # execute_mistral.yaml template, the alarm should cause execution
            # of the workflow
            details = self._create_doctor_event_details(hostname, DOWN)
            self._post_event(details)

            # Wait for the alarm to be raised
            self.assertTrue(
                self._wait_for_status(10,
                                      self._check_num_vitrage_alarms,
                                      num_alarms=num_alarms + 1))

            # Wait for the Mistral workflow execution
            self.assertTrue(
                self._wait_for_status(20,
                                      self._check_mistral_workflow_execution,
                                      num_executions=num_executions + 1))

        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._rollback_to_default(WF_NAME, num_workflows,
                                      hostname, num_alarms)
            pass

    def _rollback_to_default(self, workflow_name, num_workflows,
                             hostname, num_alarms):
        # Delete the workflow
        self.mistral_client.workflows.delete(workflow_name)

        workflows = self.mistral_client.workflows.list()
        self.assertIsNotNone(workflows)
        self.assertThat(workflows, HasLength(num_workflows))

        # Clear the host down event and wait for the alarm to be deleted
        details = self._create_doctor_event_details(hostname, UP)
        self._post_event(details)

        self.assertTrue(
            self._wait_for_status(10,
                                  self._check_num_vitrage_alarms,
                                  num_alarms=num_alarms))

    def _check_num_vitrage_alarms(self, num_alarms):
        if len(self.vitrage_client.alarm.list(vitrage_id='all',
                                              all_tenants=True)) == num_alarms:
            return True
        return False

    def _check_mistral_workflow_execution(self, num_executions):
        if len(self.mistral_client.executions.list()) == num_executions:
            return True
        return False
