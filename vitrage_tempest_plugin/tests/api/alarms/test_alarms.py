# Copyright 2016 Nokia
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import json

from oslo_log import log as logging
from testtools import matchers

from vitrage_tempest_plugin.tests.api.alarms.base import BaseAlarmsTest
from vitrage_tempest_plugin.tests.base import IsNotEmpty
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils

LOG = logging.getLogger(__name__)


class TestAlarms(BaseAlarmsTest):
    """Alarms test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestAlarms, cls).setUpClass()
        cls._template = v_utils.add_template('nagios_alarm_for_alarms.yaml')

    # noinspection PyPep8Naming
    @classmethod
    def tearDownClass(cls):
        if cls._template is not None:
            v_utils.delete_template(cls._template['uuid'])

    def _compare_alarms_lists(self, api_alarms, cli_alarms,
                              resource_type, resource_id):
        """Validate alarm existence """
        self.assertThat(api_alarms, IsNotEmpty(),
                        'The alarms list taken from api is empty')
        self.assertThat(cli_alarms, IsNotEmpty(),
                        'The alarms list taken from cli is empty')

        LOG.info("The alarms list taken from cli is : " +
                 str(cli_alarms))
        LOG.info("The alarms list taken by api is : " +
                 str(json.dumps(api_alarms)))

        cli_items = cli_alarms.splitlines()

        api_by_type = g_utils.all_matches(
            api_alarms, vitrage_type=resource_type)
        cli_by_type = cli_alarms.count(' ' + resource_type + ' ')

        api_by_id = g_utils.all_matches(api_alarms, resource_id=resource_id)
        cli_by_id = cli_alarms.count(resource_id)

        self.assertEqual(len(cli_items), len(api_alarms) + 4)
        self.assertThat(api_by_type, matchers.HasLength(cli_by_type))
        self.assertThat(api_by_id, matchers.HasLength(cli_by_id))
