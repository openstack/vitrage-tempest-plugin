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
from threading import Thread
import time

from oslo_log import log as logging
from tempest import config


from vitrage_tempest_plugin.tests.common.constants import VertexProperties
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils
from vitrage_tempest_plugin.tests.e2e.test_actions_base import TestActionsBase
from vitrage_tempest_plugin.tests import utils

CONF = config.CONF
LOG = logging.getLogger(__name__)

DEDUCED_1 = 'mock_datasource.3rd_degree_scenarios.deduced.alarm1'
DEDUCED_2 = 'mock_datasource.3rd_degree_scenarios.deduced.alarm2'
TEMPLATE_NAME = 'mock_datasource_3rd_degree_scenarios.yaml'
SLEEP = 100
MAX_FAIL_OVER_TIME = 20


class TestLongProcessing(TestActionsBase):

    @classmethod
    def setUpClass(cls):
        super(TestLongProcessing, cls).setUpClass()
        if v_utils.get_first_template(name=TEMPLATE_NAME):
            v_utils.delete_template(name=TEMPLATE_NAME)
            time.sleep(SLEEP)

    @utils.tempest_logger
    def test_high_availability_events(self):
        """The purpose of the test is to check that events are stored

        That is, during different stages in vitrage-graph lifetime:
        before graph read from db (during init)
        after graph read from db (during init)
        during get_all
        after get_all
        """
        try:
            # adding a template just to create more load (to slow things down)
            v_utils.add_template(TEMPLATE_NAME)
            time.sleep(SLEEP)
            self.keep_sending_events = True
            self.num_of_sent_events = 0

            doctor_events_thread = self._async_doctor_events()
            time.sleep(10)
            v_utils.stop_graph()
            time.sleep(10)
            v_utils.restart_graph()
            time.sleep(MAX_FAIL_OVER_TIME)
            v_utils.delete_template(name=TEMPLATE_NAME)

            # sleep to allow get_all to start and finish at least once:
            time.sleep(4 * CONF.root_cause_analysis_service.snapshots_interval)

            v_utils.restart_graph()
            self.keep_sending_events = False
            time.sleep(MAX_FAIL_OVER_TIME)
            doctor_events_thread.join(timeout=10)

            alarm_count = TempestClients.vitrage().alarm.count(
                all_tenants=True)
            self.assertTrue(self.num_of_sent_events > 0,
                            'Test did not create events')
            self.assertEqual(
                self.num_of_sent_events,
                alarm_count['CRITICAL'],
                'CRITICAL doctor events expected')

        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._remove_doctor_events()
            if v_utils.get_first_template(name=TEMPLATE_NAME):
                v_utils.delete_template(name=TEMPLATE_NAME)
            time.sleep(SLEEP)

    @utils.tempest_logger
    def test_db_init(self):
        try:
            v_utils.add_template(TEMPLATE_NAME)
            time.sleep(SLEEP)

            # 1. check template works well
            self._check_template_instance_3rd_degree_scenarios()

            # 2. check fast fail-over - start from database
            topo1 = TempestClients.vitrage().topology.get(all_tenants=True)
            v_utils.restart_graph()
            time.sleep(MAX_FAIL_OVER_TIME)
            for i in range(5):
                self._check_template_instance_3rd_degree_scenarios()
                topo2 = TempestClients.vitrage().topology.get(all_tenants=True)
                self.assert_graph_equal(
                    topo1, topo2, 'comparing graph items iteration ' + str(i))
                time.sleep(CONF.root_cause_analysis_service.snapshots_interval)

            v_utils.delete_template(name=TEMPLATE_NAME)
            time.sleep(SLEEP)
            self._check_template_instance_3rd_degree_scenarios_deleted()

        except Exception as e:
            self._handle_exception(e)
            if v_utils.get_first_template(name=TEMPLATE_NAME):
                v_utils.delete_template(name=TEMPLATE_NAME)
                time.sleep(SLEEP)
            raise

    def _check_template_instance_3rd_degree_scenarios(self):

        try:
            alarm_count = TempestClients.vitrage().alarm.count(
                all_tenants=True)
            self.assertEqual(
                CONF.root_cause_analysis_service.instances_per_host,
                alarm_count['SEVERE'],
                'Each instance should have one SEVERE deduced alarm')
            self.assertEqual(
                CONF.root_cause_analysis_service.instances_per_host,
                alarm_count['CRITICAL'],
                'Each instance should have one CRITICAL deduced alarm')

            expected_rca = [{VertexProperties.VITRAGE_TYPE: 'zabbix'}] * self.\
                conf.mock_graph_datasource.zabbix_alarms_per_host
            expected_rca.extend([{'name': DEDUCED_1}, {'name': DEDUCED_2}])

            def check_rca(alarm):
                rca = TempestClients.vitrage().rca.get(alarm['vitrage_id'],
                                                       all_tenants=True)
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
            v_utils.delete_template(name=TEMPLATE_NAME)
            self._handle_exception(e)
            raise

    def _check_template_instance_3rd_degree_scenarios_deleted(self):
        alarm_count = TempestClients.vitrage().alarm.count(
            all_tenants=True)
        self.assertEqual(
            0,
            alarm_count['SEVERE'],
            'found SEVERE deduced alarms after template delete')
        self.assertEqual(
            0,
            alarm_count['CRITICAL'],
            'found CRITICAL deduced alarms after template delete')

    def assert_graph_equal(self, g1, g2, msg):
        """Checks that two graphs are equals.

        This relies on assert_dict_equal when comparing the nodes and the
        edges of each graph.
        """
        g1_nodes = g1['nodes']
        g1_links = g1['links']

        g2_nodes = g2['nodes']
        g2_links = g1['links']

        to_remove = {'vitrage_sample_timestamp',
                     'update_timestamp',
                     'graph_index'}

        self._remove_keys_from_dicts(g1_nodes, g2_nodes, to_remove)

        self.assertItemsEqual(g1_nodes, g2_nodes,
                              msg + "Nodes of each graph are not equal")
        self.assert_items_equal(g1_links, g2_links,
                                "Edges of each graph are not equal")

    def _remove_keys_from_dicts(self, dictionaries1,
                                dictionaries2, keys_to_remove):
        self._delete_keys_from_dict(dictionaries1, keys_to_remove)
        self._delete_keys_from_dict(dictionaries2, keys_to_remove)

    @staticmethod
    def _delete_keys_from_dict(dictionaries, keys_to_remove):
        for dictionary in dictionaries:
            for key in keys_to_remove:
                if key in dictionary:
                    del dictionary[key]

    def _async_doctor_events(self, spacing=1):

        def do_create():
            while self.keep_sending_events:
                try:
                    v_utils.generate_fake_host_alarm(
                        'nova.host-0-nova.zone-0-openstack.cluster-0',
                        'test_high_availability_events' +
                        str(self.num_of_sent_events))
                    self.num_of_sent_events += 1
                    time.sleep(spacing)
                except Exception:
                    time.sleep(spacing)
                    continue

        t = Thread(target=do_create)
        t.setDaemon(True)
        t.start()
        return t

    def _remove_doctor_events(self):

        for i in range(self.num_of_sent_events):
            try:
                v_utils.generate_fake_host_alarm(
                    'nova.host-0-nova.zone-0-openstack.cluster-0',
                    'test_high_availability_events' + str(i),
                    enabled=False)
            except Exception:
                continue
