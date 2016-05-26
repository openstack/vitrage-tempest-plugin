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
from vitrage.datasources import AODH_DATASOURCE
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


class TestRca(BaseAlarmsTest):
    """RCA test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestRca, cls).setUpClass()

    def test_compare_cil_and_api(self):
        """compare_cil_and_api test

        There test validate correctness of rca of created
        aodh event alarms, and compare them with cli rca
        """
        try:
            instances = self._create_instances(num_instances=1)
            if not instances:
                LOG.error('Failed to create instance', False)
                return False

            instance_alarm = self._create_alarm(
                resource_id=utils.uni2str(text=instances[0].id),
                alarm_name='instance_rca_alarm', unic=True)

            vitrage_id = self._get_value(
                instance_alarm, VProps.VITRAGE_ID)
            api_rca = self.vitrage_client.rca.get(alarm_id=vitrage_id)
            cli_rca = utils.run_vitrage_command(
                'vitrage rca show ' + vitrage_id, self.conf)

            self.assertTrue(self._compare_rca(api_rca, cli_rca))
        except Exception:
            LOG.error('Got exception', False)
        finally:
            self._clean_all()

    def test_validate_rca(self):
        """validate_rca test

        There tests validates correctness of rca of created aodh
        event alarm and correctness of relationship between host alarm
        to instance alarms (created by special template file),
        source alarm - aodh alarm on host
        target alarms - 2 instance alarms (caused 2 created instance)
        """
        try:
            self._create_instances(num_instances=2)
            host_alarm = self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME,
                unic=False)
            api_rca = self.vitrage_client.rca.get(
                alarm_id=self._get_value(host_alarm,
                                         VProps.VITRAGE_ID))

            self.assertTrue(self._validate_rca(rca=api_rca['nodes']))
            self.assertTrue(self._validate_relationship(
                links=api_rca['links'],
                alarms=api_rca['nodes']))
        except Exception:
            LOG.error('Got exception', False)
        finally:
            self._clean_all()

    def test_validate_deduce_alarms(self):
        """validate_deduce_alarms test

        There tests validates correctness of deduce alarms
        (created by special template file), and compare there
        resource_id with created instances id
        """
        try:
            instances = self._create_instances(num_instances=2)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            api_alarms = self.vitrage_client.alarms.list(vitrage_id=None)

            self.assertTrue(self._validate_deduce_alarms(
                alarms=api_alarms,
                instances=instances))
        except Exception:
            LOG.error('Got exception', False)
        finally:
            self._clean_all()

    def test_validate_set_state(self):
        """validate_set_state test

        There tests validates correctness of topology resource
        state, after alarms creation (by special template file),
        source state - ERROR
        target state - SUBOPTIMAL (caused 2 created instance)
        """
        try:
            instances = self._create_instances(num_instances=2)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            topology = self.vitrage_client.topology.get()

            self.assertTrue(self._validate_set_state(
                topology=topology['nodes'],
                instances=instances))
        except Exception:
            LOG.error('Got exception', False)
        finally:
            self._clean_all()

    def test_validate_notifier(self):
        """validate_notifier test

        There tests validates work of aodh alarm notifier -
        all created vitrage alarms appears in ceilometer
        alarms-list.
        IMPORTANT: enable notifiers=aodh in vitrage.conf file
        """
        try:
            self._create_instances(num_instances=2)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            vitrage_alarms = self.vitrage_client.alarms.list(vitrage_id=None)
            ceilometer_alarms = self.ceilometer_client.alarms.list()

            self.assertTrue(self._validate_notifier(
                alarms=ceilometer_alarms,
                vitrage_alarms=vitrage_alarms))
        except Exception:
            LOG.error('Got exception', False)
        finally:
            self._clean_all()

    def _clean_all(self):
        self._delete_instances()
        self._delete_ceilometer_alarms()

    def _create_alarm(self, resource_id, alarm_name, unic=False):
        if not resource_id:
            raise Exception("Can't create alarm with empty resource id")

        self._create_ceilometer_alarm(resource_id=resource_id,
                                      name=alarm_name, unic=unic)

        list_alarms = self.vitrage_client.alarms.list(vitrage_id=None)
        expected_alarm = self._filter_alarms_by_parameter(
            list_alarms, ['resource_id', 'type'],
            [resource_id, AODH_DATASOURCE])
        if not expected_alarm:
            return None
        return expected_alarm[0]

    def _compare_rca(self, api_rca, cli_rca):
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
        if not rca:
            LOG.error("The alarms list is empty")
            return False

        LOG.debug("The rca alarms list is : %s",
                  json.dumps(rca))

        resource_alarm = self._filter_alarms_by_parameter(
            rca, ['type', 'name'],
            [AODH_DATASOURCE, RCA_ALARM_NAME])

        deduce_alarms = self._filter_alarms_by_parameter(
            rca, ['type', 'name', 'severity'],
            [VITRAGE_TYPE, VITRAGE_ALARM_NAME,
             OperationalAlarmSeverity.WARNING])

        return (len(rca) == 3 and
                len(resource_alarm) == 1 and
                len(deduce_alarms) == 2)

    def _validate_deduce_alarms(self, alarms, instances):
        """Validate alarm existence """
        if not alarms:
            LOG.error("The alarms list is empty")
            return False

        LOG.debug("The alarms list is : %s",
                  json.dumps(alarms))

        deduce_alarms_1 = self._filter_alarms_by_parameter(
            alarms,
            ['type', 'name', 'resource_type', 'resource_id'],
            [VITRAGE_TYPE, VITRAGE_ALARM_NAME,
             NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(instances[0].id)])

        deduce_alarms_2 = self._filter_alarms_by_parameter(
            alarms,
            ['type', 'name', 'resource_type', 'resource_id'],
            [VITRAGE_TYPE, VITRAGE_ALARM_NAME,
             NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(instances[1].id)])

        return (len(alarms) == 3 and
                len(deduce_alarms_1) == 1 and
                len(deduce_alarms_2) == 1)

    def _validate_relationship(self, links, alarms):
        if not links:
            LOG.error("The links list is empty")
            return False

        if not alarms:
            LOG.error("The alarms list is empty")
            return False

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

        return flag and len(alarms) == 3

    def _validate_set_state(self, topology, instances):
        if not topology:
            LOG.error("The topology list is empty")
            return False

        host = self._filter_alarms_by_parameter(
            topology,
            [VProps.TYPE, VProps.ID, VProps.VITRAGE_STATE,
             VProps.AGGREGATED_STATE],
            [NOVA_HOST_DATASOURCE,
             self._get_hostname(),
             OperationalResourceState.ERROR,
             OperationalResourceState.ERROR])

        vm1 = self._filter_alarms_by_parameter(
            topology,
            [VProps.TYPE, VProps.ID, VProps.VITRAGE_STATE,
             VProps.AGGREGATED_STATE],
            [NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(instances[0].id),
             OperationalResourceState.SUBOPTIMAL,
             OperationalResourceState.SUBOPTIMAL])

        vm2 = self._filter_alarms_by_parameter(
            topology,
            [VProps.TYPE, VProps.ID, VProps.VITRAGE_STATE,
             VProps.AGGREGATED_STATE],
            [NOVA_INSTANCE_DATASOURCE,
             utils.uni2str(instances[1].id),
             OperationalResourceState.SUBOPTIMAL,
             OperationalResourceState.SUBOPTIMAL])

        return len(host) == 1 and len(vm1) == 1 and len(vm2) == 1

    @staticmethod
    def _validate_notifier(alarms, vitrage_alarms):
        if not alarms:
            LOG.error("The alarms list is empty")
            return False

        if not vitrage_alarms:
            LOG.error("The vitrage alarms list is empty")
            return False

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
        return (len(vitrage_alarms) == validation
                and len(alarms) == 3)

    @staticmethod
    def _clean_timestamps(alist):
        try:
            del alist[5][1][0][VProps.SAMPLE_TIMESTAMP]
            del alist[5][1][0][VProps.UPDATE_TIMESTAMP]
        except Exception:
            pass
        return alist

    def _get_hostname(self):
        return self._get_value(item=self._get_host(), key=VProps.ID)
