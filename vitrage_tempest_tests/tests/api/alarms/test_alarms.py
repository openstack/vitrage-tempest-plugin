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

from vitrage.datasources.nova.host import NOVA_HOST_DATASOURCE
from vitrage.datasources.nova.instance import NOVA_INSTANCE_DATASOURCE

from vitrage_tempest_tests.tests.api.base import BaseApiTest
import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)


class BaseAlarmsTest(BaseApiTest):
    """Alarms test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseAlarmsTest, cls).setUpClass()

    ''''  Nova instances have alarms due to deduced alarm template: '''''
    ''''    nova_alarm_for_every_host.yaml '''''
    ''''    nova_alarm_for_every_instance.yaml '''''
    ''''  Nagios alarm template is nagios_alarm.yaml '''''

    @staticmethod
    def copy_alarms_templates_files():
        utils.run_from_terminal(
            "cp " +
            "vitrage_tempest_tests/tests/resources/templates/"
            + "*_alarm* /etc/vitrage/templates/.")

    @staticmethod
    def delete_alarms_templates_files():
        utils.run_from_terminal(
            "rm /etc/vitrage/templates/*_alarm*")

    def test_compare_alarms(self):
        """Wrapper that returns a test graph."""
        self._create_instances(num_instances=3)
        api_alarms = self.vitrage_client.alarms.list(vitrage_id=None)
        cli_alarms = utils.run_vitrage_command('vitrage alarms list')
        self.assertEqual(True,
                         self._compare_alarms_lists(api_alarms, cli_alarms))
        self._delete_instances()

    def test_nova_alarms(self):
        """Wrapper that returns test nova alarms."""
        self._create_instances(num_instances=4)
        resources = self.nova_client.servers.list()

        alarms = self.vitrage_client.alarms.list(vitrage_id=None)
        nova_alarms = self._filter_alarms_by_resource_type(
            alarms, NOVA_INSTANCE_DATASOURCE)
        self.assertEqual(True, self._validate_alarms_correctness(nova_alarms,
                                                                 resources))
        self._delete_instances()

    # def test_nagios_alarms(self):
    #     """Wrapper that returns test nagios alarms."""
    #     alarms = self.vitrage_client.alarms.list()
    #     nagios_alarms = self._filter_alarms_by_resource_type(alarms,
    #                                                          'nagios')
    #     self.assertEqual(True, self._validate_alarms_correctness(
    #         nagios_alarms, 'nagios'))

    # def test_aodh_alarms(self):
    #     """Wrapper that returns test aodh alarms."""
    #     # self.create_alarms_per_component('aodh')
    #     alarms = self.vitrage_client.alarms.list()
    #     aodh_alarms = self._filter_alarms_by_resource_type(alarms,
    #                                                       'aodh')
    #     self.assertEqual(True, self._validate_alarms_correctness(
    #         aodh_alarms, 'aodh'))

    def _compare_alarms_lists(self, api_alarms, cli_alarms):
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

        cli_items = cli_alarms.count('vitrage')
        nova_instance_alarms = \
            self._filter_alarms_by_resource_type(api_alarms,
                                                 NOVA_INSTANCE_DATASOURCE)
        nova_instances = cli_alarms.count(NOVA_INSTANCE_DATASOURCE)
        nova_host_alarms = \
            self._filter_alarms_by_resource_type(api_alarms,
                                                 NOVA_HOST_DATASOURCE)
        nova_hosts = cli_alarms.count(NOVA_HOST_DATASOURCE)
        return (cli_items == len(api_alarms) and
                nova_instances == len(nova_instance_alarms) and
                nova_hosts == len(nova_host_alarms))

    @staticmethod
    def _validate_alarms_correctness(alarms, resources):
        """Validate alarm existence """
        if not alarms:
            LOG.error("The alarms list is empty")
            return False
        if not resources:
            LOG.error("The resources list is empty")
            return False

        count = 0
        for resource in resources:
            LOG.info("______________________")
            LOG.info("The resource id is %s", resource.id)
            for item in alarms:
                LOG.info("The alarms resource id is %s", item["resource_id"])
                if item["resource_id"] == resource.id:
                    count += 1

        LOG.info("The resources list size is %s", len(resources))
        LOG.info("The common items list size is %s", count)
        return count == len(resources)

    @staticmethod
    def _filter_alarms_by_resource_type(alarms_list, alarm_type):
        filtered_alarms_list = []
        for item in alarms_list:
            if item["category"] == "ALARM" \
                    and item["resource_type"] == alarm_type:
                filtered_alarms_list.append(item)

        return filtered_alarms_list
