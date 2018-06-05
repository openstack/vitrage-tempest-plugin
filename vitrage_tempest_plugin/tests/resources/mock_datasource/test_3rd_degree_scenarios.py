# Copyright 2018 - Nokia
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
from concurrent import futures
import time

from oslo_log import log as logging

from vitrage_tempest_plugin.tests.common.constants import VertexProperties
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils
from vitrage_tempest_plugin.tests.e2e.test_actions_base import TestActionsBase
from vitrage_tempest_plugin.tests import utils

LOG = logging.getLogger(__name__)

DEDUCED_1 = 'mock_datasource.3rd_degree_scenarios.deduced.alarm1'
DEDUCED_2 = 'mock_datasource.3rd_degree_scenarios.deduced.alarm2'
SLEEP = 80


class TestLongProcessing(TestActionsBase):

    @classmethod
    def setUpClass(cls):
        super(TestLongProcessing, cls).setUpClass()
        v_utils.delete_template(
            name="mock_datasource_3rd_degree_scenarios.yaml")
        time.sleep(SLEEP)

    @utils.tempest_logger
    def test_3rd_degree_scenarios(self):
        try:
            v_utils.add_template("mock_datasource_3rd_degree_scenarios.yaml")
            time.sleep(SLEEP)

            self._check_template_instance_3rd_degree_scenarios()
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            v_utils.delete_template(
                name="mock_datasource_3rd_degree_scenarios.yaml")
            time.sleep(SLEEP)

    @utils.tempest_logger
    def test_3rd_degree_scenarios_init_procedure(self):

        try:
            v_utils.add_template("mock_datasource_3rd_degree_scenarios.yaml")
            time.sleep(SLEEP)

            v_utils.restart_graph()
            time.sleep(SLEEP)

            self._check_template_instance_3rd_degree_scenarios()
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            v_utils.delete_template(
                name="mock_datasource_3rd_degree_scenarios.yaml")
            time.sleep(SLEEP)

    def _check_template_instance_3rd_degree_scenarios(self):

        try:
            alarm_count = TempestClients.vitrage().alarm.count(
                all_tenants=True)
            self.assertEqual(
                self.conf.mock_graph_datasource.instances_per_host,
                alarm_count['SEVERE'],
                'Each instance should have one SEVERE deduced alarm')
            self.assertEqual(
                self.conf.mock_graph_datasource.instances_per_host,
                alarm_count['CRITICAL'],
                'Each instance should have one CRITICAL deduced alarm')

            expected_rca = [{VertexProperties.VITRAGE_TYPE: 'zabbix'}] * self.\
                conf.mock_graph_datasource.zabbix_alarms_per_host
            expected_rca.extend([{'name': DEDUCED_1}, {'name': DEDUCED_2}])

            def check_rca(alarm):
                rca = TempestClients.vitrage().rca.get(alarm['vitrage_id'])
                try:
                    self._check_rca(rca, expected_rca, alarm)
                    return True
                except Exception as e:
                    LOG.exception('check_rca failed', e)
                    return False

            # 10 threads calling rca api
            alarms = TempestClients.vitrage().alarm.list(all_tenants=True,
                                                         vitrage_id='all')
            deduced_alarms = g_utils.all_matches(
                alarms, vitrage_type='vitrage', name=DEDUCED_2)
            workers = futures.ThreadPoolExecutor(max_workers=10)
            workers_result = [r for r in workers.map(check_rca,
                                                     deduced_alarms)]
            self.assertTrue(all(workers_result))

        except Exception as e:
            v_utils.delete_template(
                name="mock_datasource_3rd_degree_scenarios.yaml")
            self._handle_exception(e)
            raise
