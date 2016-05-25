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
from vitrage.datasources.aodh import AODH_DATASOURCE

from vitrage_tempest_tests.tests.api.alarms.base import BaseAlarmsTest

import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)


class TestAlarms(BaseAlarmsTest):
    """Alarms test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestAlarms, cls).setUpClass()

    def test_compare_cli_vs_api_alarms(self):
        """Wrapper that returns a test graph."""
        try:
            resources = self._create_instances(num_instances=1)
            self._create_ceilometer_alarm(resource_id=resources[0].id,
                                          name='tempest_aodh_test')

            api_alarms = self.vitrage_client.alarms.list(vitrage_id=None)
            cli_alarms = utils.run_vitrage_command(
                'vitrage alarms list', self.conf)
            self.assertTrue(self._compare_alarms_lists(
                api_alarms, cli_alarms, AODH_DATASOURCE,
                utils.uni2str(resources[0].id)))

        finally:
            self._delete_ceilometer_alarms()
            self._delete_instances()

    def _compare_alarms_lists(self, api_alarms, cli_alarms,
                              resource_type, resource_id):
        """Validate alarm existence """
        if not api_alarms:
            LOG.error("The alarms list taken from api is empty")
            return False
        if cli_alarms is None:
            LOG.error("The alarms list taken from cli is empty")
            return False

        LOG.debug("The alarms list taken from cli is : %s", cli_alarms)
        LOG.debug("The alarms list taken by api is : %s",
                  json.dumps(api_alarms))

        cli_items = cli_alarms.splitlines()

        api_by_type = self._filter_alarms_by_parameter(
            api_alarms, ['type'], [resource_type])
        cli_by_type = cli_alarms.count(' ' + resource_type + ' ')

        api_by_id = self._filter_alarms_by_parameter(
            api_alarms, ['resource_id'], [resource_id])
        cli_by_id = cli_alarms.count(resource_id)
        return (len(cli_items) - 4 == len(api_alarms) and
                cli_by_type == len(api_by_type) and
                cli_by_id == len(api_by_id))
