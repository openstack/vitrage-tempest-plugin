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

from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.aodh import AODH_DATASOURCE
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage.entity_graph.mappings.operational_alarm_severity \
    import OperationalAlarmSeverity
from vitrage.entity_graph.mappings.operational_resource_state \
    import OperationalResourceState
from vitrage.evaluator.actions.evaluator_event_transformer \
    import VITRAGE_TYPE
from vitrage_tempest_tests.tests.api.alarms.base import BaseAlarmsTest
import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)
RCA_ALARM_NAME = 'rca_test_host_alarm'
VITRAGE_ALARM_NAME = 'instance_deduce'


class BaseRcaTest(BaseAlarmsTest):

    @classmethod
    def setUpClass(cls):
        super(BaseRcaTest, cls).setUpClass()

    def _clean_all(self):
        self._delete_instances()
        self._delete_ceilometer_alarms()

    def _create_alarm(self, resource_id, alarm_name, unic=False):
        self._create_ceilometer_alarm(resource_id=resource_id,
                                      name=alarm_name, unic=unic)

        list_alarms = self.vitrage_client.alarm.list(vitrage_id=None)
        expected_alarm = self._filter_list_by_pairs_parameters(
            list_alarms, ['resource_id', VProps.TYPE],
            [resource_id, AODH_DATASOURCE])
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

        resource_alarm = self._filter_list_by_pairs_parameters(
            rca, [VProps.TYPE, VProps.NAME],
            [AODH_DATASOURCE, RCA_ALARM_NAME])

        deduce_alarms = self._filter_list_by_pairs_parameters(
            rca, [VProps.TYPE, VProps.NAME, VProps.SEVERITY],
            [VITRAGE_TYPE, VITRAGE_ALARM_NAME,
             OperationalAlarmSeverity.WARNING])

        self.assertEqual(len(rca), 3)
        self.assertEqual(len(resource_alarm), 1)
        self.assertEqual(len(deduce_alarms), 2)

    def _validate_deduce_alarms(self, alarms, instances):
        """Validate alarm existence """
        self.assertNotEqual(len(alarms), 0, 'The alarms list is empty')
        LOG.info("The alarms list is : " + str(json.dumps(alarms)))

        deduce_alarms_1 = self._filter_list_by_pairs_parameters(
            alarms,
            [VProps.TYPE, VProps.NAME, 'resource_type', 'resource_id'],
            [VITRAGE_TYPE, VITRAGE_ALARM_NAME,
             NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(instances[0].id)])

        deduce_alarms_2 = self._filter_list_by_pairs_parameters(
            alarms,
            [VProps.TYPE, VProps.NAME, 'resource_type', 'resource_id'],
            [VITRAGE_TYPE, VITRAGE_ALARM_NAME,
             NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(instances[1].id)])

        self.assertEqual(len(alarms), 3)
        self.assertEqual(len(deduce_alarms_1), 1)
        self.assertEqual(len(deduce_alarms_2), 1)

    def _validate_relationship(self, links, alarms):
        self.assertNotEqual(len(links), 0, 'The links list is empty')
        self.assertNotEqual(len(alarms), 0, 'The alarms list is empty')

        flag = True
        for item in links:
            source_alarm_name = self._get_value(
                alarms[item['source']], VProps.NAME)
            target_alarm_name = self._get_value(
                alarms[item['target']], VProps.NAME)
            if self._get_value(item, 'key') != 'causes' \
                    or self._get_value(item, 'relationship_type') != 'causes' \
                    or source_alarm_name != RCA_ALARM_NAME \
                    or target_alarm_name != VITRAGE_ALARM_NAME:
                flag = False

        self.assertEqual(len(alarms), 3)
        self.assertTrue(flag)

    def _validate_set_state(self, topology, instances):
        self.assertNotEqual(len(topology), 0, 'The topology graph is empty')

        host = self._filter_list_by_pairs_parameters(
            topology,
            [VProps.TYPE, VProps.ID, VProps.VITRAGE_STATE,
             VProps.AGGREGATED_STATE],
            [NOVA_HOST_DATASOURCE,
             self._get_hostname(),
             OperationalResourceState.ERROR,
             OperationalResourceState.ERROR])

        vm1 = self._filter_list_by_pairs_parameters(
            topology,
            [VProps.TYPE, VProps.ID, VProps.VITRAGE_STATE,
             VProps.AGGREGATED_STATE],
            [NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(instances[0].id),
             OperationalResourceState.SUBOPTIMAL,
             OperationalResourceState.SUBOPTIMAL])

        vm2 = self._filter_list_by_pairs_parameters(
            topology,
            [VProps.TYPE, VProps.ID, VProps.VITRAGE_STATE,
             VProps.AGGREGATED_STATE],
            [NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(instances[1].id),
             OperationalResourceState.SUBOPTIMAL,
             OperationalResourceState.SUBOPTIMAL])

        self.assertEqual(len(host), 1)
        self.assertEqual(len(vm1), 1)
        self.assertEqual(len(vm2), 1)

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

        self.assertEqual(len(vitrage_alarms), validation)
        self.assertEqual(len(alarms), 3)

    def _get_hostname(self):
        return self._get_value(item=self._get_host(), key=VProps.ID)

    @staticmethod
    def _clean_timestamps(alist):
        try:
            del alist[5][1][0][VProps.SAMPLE_TIMESTAMP]
            del alist[5][1][0][VProps.UPDATE_TIMESTAMP]
        except Exception:
            pass
        return alist
