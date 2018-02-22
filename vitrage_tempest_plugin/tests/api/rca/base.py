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

from vitrage.common.constants import EdgeLabel
from vitrage.common.constants import EdgeProperties
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.aodh import AODH_DATASOURCE
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage.entity_graph.mappings.operational_alarm_severity \
    import OperationalAlarmSeverity
from vitrage.entity_graph.mappings.operational_resource_state \
    import OperationalResourceState
from vitrage.evaluator.actions.evaluator_event_transformer \
    import VITRAGE_DATASOURCE
from vitrage_tempest_plugin.tests.api.alarms.base import BaseAlarmsTest
from vitrage_tempest_plugin.tests.common import aodh_utils
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common import nova_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils

LOG = logging.getLogger(__name__)
RCA_ALARM_NAME = 'rca_test_host_alarm'
VITRAGE_ALARM_NAME = 'instance_deduce'


class BaseRcaTest(BaseAlarmsTest):

    def setUp(self):
        super(BaseRcaTest, self).setUp()

    def tearDown(self):
        super(BaseRcaTest, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(BaseRcaTest, cls).setUpClass()

    def _clean_all(self):
        nova_utils.delete_all_instances()
        aodh_utils.delete_all_aodh_alarms()

    def _create_alarm(self, resource_id, alarm_name, unic=False):
        aodh_utils.create_aodh_alarm(resource_id=resource_id,
                                     name=alarm_name,
                                     unic=unic)

        list_alarms = self.vitrage_client.alarm.list(vitrage_id='all',
                                                     all_tenants=True)
        expected_alarm = g_utils.all_matches(
            list_alarms,
            resource_id=resource_id,
            vitrage_type=AODH_DATASOURCE)
        if not expected_alarm:
            return None
        return expected_alarm[0]

    def _compare_rca(self, api_rca, cli_rca):
        self.assertNotEqual(len(api_rca), 0, 'The rca taken from api is empty')
        self.assertIsNotNone(cli_rca, 'The rca taken from cli is empty')

        LOG.info("The rca taken from cli is : " + str(cli_rca))
        LOG.info("The rca taken by api is : " + str(json.dumps(api_rca)))

        parsed_rca = json.loads(cli_rca)
        sorted_cli_graph = self._clean_timestamps(sorted(parsed_rca.items()))
        sorted_api_graph = self._clean_timestamps(sorted(api_rca.items()))
        self.assertEqual(sorted_cli_graph, sorted_api_graph)

    def _validate_rca(self, rca):
        self.assertNotEqual(len(rca), 0, 'The rca is empty')
        LOG.info("The rca alarms list is : " + str(json.dumps(rca)))

        resource_alarm = g_utils.all_matches(
            rca,
            vitrage_type=AODH_DATASOURCE,
            name=RCA_ALARM_NAME)

        deduce_alarms = g_utils.all_matches(
            rca,
            vitrage_type=VITRAGE_DATASOURCE,
            name=VITRAGE_ALARM_NAME,
            severity=OperationalAlarmSeverity.WARNING)

        self.assertEqual(3, len(rca))
        self.assertEqual(1, len(resource_alarm))
        self.assertEqual(2, len(deduce_alarms))

    def _validate_deduce_alarms(self, alarms, instances):
        """Validate alarm existence """
        self.assertNotEqual(len(alarms), 0, 'The alarms list is empty')
        LOG.info("The alarms list is : " + str(json.dumps(alarms)))

        # Find the vitrage_id of the deduced alarms using their original id.
        vitrage_resources = TempestClients.vitrage().resource.list(
            all_tenants=False)
        vitrage_instance_0_id = g_utils.first_match(vitrage_resources,
                                                    id=instances[0].id)

        vitrage_instance_1_id = g_utils.first_match(vitrage_resources,
                                                    id=instances[1].id)

        # Find the deduced alarms based on their properties
        deduce_alarms_1 = g_utils.all_matches(
            alarms,
            vitrage_type=VITRAGE_DATASOURCE,
            name=VITRAGE_ALARM_NAME,
            vitrage_resource_type=NOVA_INSTANCE_DATASOURCE,
            vitrage_resource_id=vitrage_instance_0_id[VProps.VITRAGE_ID])

        deduce_alarms_2 = g_utils.all_matches(
            alarms,
            vitrage_type=VITRAGE_DATASOURCE,
            name=VITRAGE_ALARM_NAME,
            vitrage_resource_type=NOVA_INSTANCE_DATASOURCE,
            vitrage_resource_id=vitrage_instance_1_id[VProps.VITRAGE_ID])

        self.assertEqual(3, len(alarms), "Expected 3 alarms - 1 on host and "
                                         "2 deduced")
        self.assertEqual(1, len(deduce_alarms_1), "Deduced alarm not found")
        self.assertEqual(1, len(deduce_alarms_2), "Deduced alarm not found")

    def _validate_relationship(self, links, alarms):
        self.assertNotEqual(len(links), 0, 'The links list is empty')
        self.assertNotEqual(len(alarms), 0, 'The alarms list is empty')

        flag = True
        for item in links:
            source_alarm_name = alarms[item['source']].get(VProps.NAME)
            target_alarm_name = alarms[item['target']].get(VProps.NAME)
            if item.get('key') != EdgeLabel.CAUSES \
                    or item.get(EdgeProperties.RELATIONSHIP_TYPE) != EdgeLabel.CAUSES \
                    or source_alarm_name != RCA_ALARM_NAME \
                    or target_alarm_name != VITRAGE_ALARM_NAME:
                flag = False

        self.assertEqual(3, len(alarms))
        self.assertTrue(flag)

    def _validate_set_state(self, topology, instances):
        self.assertNotEqual(len(topology), 0, 'The topology graph is empty')
        host = g_utils.all_matches(
            topology,
            vitrage_type=NOVA_HOST_DATASOURCE,
            id=self._get_hostname(),
            vitrage_state=OperationalResourceState.ERROR,
            vitrage_aggregated_state=OperationalResourceState.ERROR)

        vm1 = g_utils.all_matches(
            topology,
            vitrage_type=NOVA_INSTANCE_DATASOURCE,
            id=instances[0].id,
            vitrage_state=OperationalResourceState.SUBOPTIMAL,
            vitrage_aggregated_state=OperationalResourceState.SUBOPTIMAL)

        vm2 = g_utils.all_matches(
            topology,
            vitrage_type=NOVA_INSTANCE_DATASOURCE,
            id=instances[1].id,
            vitrage_state=OperationalResourceState.SUBOPTIMAL,
            vitrage_aggregated_state=OperationalResourceState.SUBOPTIMAL)

        self.assertEqual(1, len(host))
        self.assertEqual(1, len(vm1))
        self.assertEqual(1, len(vm2))

    def _validate_notifier(self, alarms, vitrage_alarms):
        self.assertNotEqual(len(alarms), 0, 'The aodh alarms list is empty')
        self.assertNotEqual(len(vitrage_alarms), 0,
                            'The vitrage alarms list is empty')

        validation = 0
        for itemC in alarms:
            vitrage_id = filter(
                lambda item: item['field'] == VProps.VITRAGE_ID,
                itemC.event_rule['query'])
            for itemV in vitrage_alarms:
                if not vitrage_id:
                    if itemC.name == itemV[VProps.NAME]:
                        validation += 1
                        break
                elif vitrage_id[0]['value'] == itemV[VProps.VITRAGE_ID]:
                    validation += 1
                    break

        self.assertEqual(validation, len(vitrage_alarms))
        self.assertEqual(3, len(alarms))

    def _get_hostname(self):
        host = vitrage_utils.get_first_host()
        return host.get(VProps.ID)

    @staticmethod
    def _clean_timestamps(alist):
        try:
            del alist[5][1][0][VProps.VITRAGE_SAMPLE_TIMESTAMP]
            del alist[5][1][0][VProps.UPDATE_TIMESTAMP]
        except Exception:
            pass
        return alist
