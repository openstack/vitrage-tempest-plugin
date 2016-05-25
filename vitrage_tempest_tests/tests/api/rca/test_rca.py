# Copyright 2016 - Nokia
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
from vitrage.common.constants import VertexProperties
from vitrage.datasources import AODH_DATASOURCE
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE

from vitrage_tempest_tests.tests.api.alarms.base import BaseAlarmsTest
import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)
RCA_ALARM_NAME = 'rca_test_host_alarm'
VITRAGE_ALARM_NAME = 'instance_deduce'
VITRAGE_DATASOURCE = 'vitrage'


class TestRca(BaseAlarmsTest):
    """RCA test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestRca, cls).setUpClass()

    def test_compare_cil_and_api(self):
        try:
            vitrage_id = self._get_alarm_id(
                resource_type=NOVA_INSTANCE_DATASOURCE,
                alarm_name='instance_rca_alarm', unic=True)

            api_rca = self.vitrage_client.rca.get(alarm_id=vitrage_id)
            cli_rca = utils.run_vitrage_command(
                'vitrage rca show ' + vitrage_id, self.conf)

            self.assertTrue(self._compare_rca(api_rca, cli_rca))

        finally:
            self._delete_ceilometer_alarms()
            self._delete_instances()

    def test_validate_rca(self):
        try:
            vitrage_id = self._get_alarm_id(resource_type=NOVA_HOST_DATASOURCE,
                                            alarm_name=RCA_ALARM_NAME,
                                            unic=False)
            resources = self._create_instances(2)
            api_rca = self.vitrage_client.rca.get(alarm_id=vitrage_id)
            api_alarms = self.vitrage_client.alarms.list(vitrage_id=None)

            self.assertTrue(self._validate_rca(rca=api_rca['nodes']))
            self.assertTrue(self._validate_deduce_alarms(alarms=api_alarms,
                                                         resources=resources))
        finally:
            self._delete_ceilometer_alarms()
            self._delete_instances()

    def _get_alarm_id(self, resource_type, alarm_name, unic):
        if resource_type is NOVA_INSTANCE_DATASOURCE:
            resource = self._create_instances(num_instances=1)
            resource_id = utils.uni2str(resource[0].id)
        else:
            resource = self._get_host()
            resource_id = utils.uni2str(resource[VertexProperties.ID])

        self._create_ceilometer_alarm(resource_id=resource_id,
                                      name=alarm_name, unic=unic)

        list_alarms = self.vitrage_client.alarms.list(vitrage_id=None)
        expected_alarm = self._filter_alarms_by_parameter(
            list_alarms, ['resource_id', 'type'],
            [resource_id, AODH_DATASOURCE])
        return utils.uni2str(
            expected_alarm[0][VertexProperties.VITRAGE_ID])

    def _compare_rca(self, api_rca, cli_rca):
        """Validate alarm existence """
        if not api_rca:
            LOG.error("The rca taken from api is empty")
            return False
        if cli_rca is None:
            LOG.error("The rca taken from cli is empty")
            return False

        LOG.debug("The rca taken from cli is : %s", cli_rca)
        LOG.debug("The rca taken by api is : %s",
                  json.dumps(api_rca))

        parsed_rca = json.loads(cli_rca)
        sorted_cli_graph = self._clean_timestamps(sorted(parsed_rca.items()))
        sorted_api_graph = self._clean_timestamps(sorted(api_rca.items()))
        return sorted_cli_graph == sorted_api_graph

    def _validate_rca(self, rca):
        """Validate alarm existence """
        if not rca:
            LOG.error("The alarms list is empty")
            return False

        LOG.debug("The rca alarms list is : %s",
                  json.dumps(rca))

        resource_alarm = self._filter_alarms_by_parameter(
            rca, ['type', 'name'],
            [AODH_DATASOURCE, RCA_ALARM_NAME])

        deduce_alarms = self._filter_alarms_by_parameter(
            rca, ['type', 'name'],
            [VITRAGE_DATASOURCE, VITRAGE_ALARM_NAME])

        return (len(resource_alarm) == 1 and
                len(deduce_alarms) == 2)

    def _validate_deduce_alarms(self, alarms, resources):
        """Validate alarm existence """
        if not alarms:
            LOG.error("The alarms list is empty")
            return False

        LOG.debug("The alarms list is : %s",
                  json.dumps(alarms))

        deduce_alarms_1 = self._filter_alarms_by_parameter(
            alarms,
            ['type', 'name', 'resource_type', 'resource_id'],
            [VITRAGE_DATASOURCE, VITRAGE_ALARM_NAME,
             NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(resources[0].id)])

        deduce_alarms_2 = self._filter_alarms_by_parameter(
            alarms,
            ['type', 'name', 'resource_type', 'resource_id'],
            [VITRAGE_DATASOURCE, VITRAGE_ALARM_NAME,
             NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(resources[1].id)])

        return (len(deduce_alarms_1) == 1 and
                len(deduce_alarms_2) == 1)

    @staticmethod
    def _clean_timestamps(alist):
        try:
            del alist[5][1][0][VertexProperties.SAMPLE_TIMESTAMP]
            del alist[5][1][0][VertexProperties.UPDATE_TIMESTAMP]
        except Exception:
            pass
        return alist
