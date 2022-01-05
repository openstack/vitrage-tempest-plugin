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
import testtools

from oslo_log import log as logging
from vitrage_tempest_plugin.tests import utils

from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrage_tempest_plugin.tests.common import aodh_utils
from vitrage_tempest_plugin.tests.common import nova_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients

LOG = logging.getLogger(__name__)


class TestAodhAlarm(BaseVitrageTempest):
    NUM_INSTANCE = 1
    NUM_ALARM = 1

    def tearDown(self):
        super(TestAodhAlarm, self).tearDown()
        aodh_utils.delete_all_aodh_alarms()
        aodh_utils.delete_all_gnocchi_metrics()
        nova_utils.delete_all_instances()

    @utils.tempest_logger
    def test_alarm_with_resource_id(self):
        # Action
        nova_utils.create_instances(num_instances=self.NUM_INSTANCE)
        aodh_utils.create_aodh_alarm(self._find_instance_resource_id())
        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(all_tenants=True)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1,
            host_edges=1 + self.NUM_INSTANCE,
            instance_entities=self.NUM_INSTANCE,
            instance_edges=2 * self.NUM_INSTANCE + self.NUM_ALARM,
            aodh_entities=self.NUM_ALARM,
            aodh_edges=self.NUM_ALARM)
        num_entities = self.num_default_entities + \
            2 * self.NUM_INSTANCE + self.NUM_ALARM + \
            self.num_default_networks + self.num_default_ports
        num_edges = self.num_default_edges + 3 * self.NUM_INSTANCE + \
            self.NUM_ALARM + self.num_default_ports

        # Test Assertions
        self._validate_graph_correctness(graph,
                                         num_entities,
                                         num_edges,
                                         entities)

    @utils.tempest_logger
    def test_gnocchi_aggregation_by_metrics_threshold_alarm(self):
        # Action
        nova_utils.create_instances(num_instances=self.NUM_INSTANCE)
        aodh_utils.create_aodh_metrics_threshold_alarm()

        api_graph = self.vitrage_client.topology.get(all_tenants=True)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1,
            host_edges=1 + self.NUM_INSTANCE,
            instance_entities=self.NUM_INSTANCE,
            instance_edges=2 * self.NUM_INSTANCE,
            aodh_entities=self.NUM_ALARM,
            aodh_edges=0)
        num_entities = self.num_default_entities + \
            2 * self.NUM_INSTANCE + self.NUM_ALARM + \
            self.num_default_networks + self.num_default_ports
        num_edges = self.num_default_edges + 3 * self.NUM_INSTANCE + \
            self.num_default_ports

        self._validate_graph_correctness(graph,
                                         num_entities,
                                         num_edges,
                                         entities)

    @testtools.skip('gnocchi sometime fails here ignore for now')
    @utils.tempest_logger
    def test_gnocchi_aggregation_by_resources_threshold(self):
        # Action
        nova_utils.create_instances(num_instances=self.NUM_INSTANCE)
        aodh_utils.create_aodh_resources_threshold_alarm(
            resource_id=self._find_instance_resource_id())

        api_graph = self.vitrage_client.topology.get(all_tenants=True)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1,
            host_edges=1 + self.NUM_INSTANCE,
            instance_entities=self.NUM_INSTANCE,
            instance_edges=2 * self.NUM_INSTANCE + self.NUM_ALARM,
            aodh_entities=self.NUM_ALARM,
            aodh_edges=self.NUM_ALARM)
        num_entities = self.num_default_entities + \
            2 * self.NUM_INSTANCE + self.NUM_ALARM + \
            self.num_default_networks + self.num_default_ports
        num_edges = self.num_default_edges + 3 * self.NUM_INSTANCE + \
            + self.NUM_ALARM + self.num_default_ports

        self._validate_graph_correctness(graph,
                                         num_entities,
                                         num_edges,
                                         entities)

    @utils.tempest_logger
    def test_alarm_without_resource_id(self):
        # Action
        aodh_utils.create_aodh_alarm()

        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(all_tenants=True)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1,
            host_edges=1,
            aodh_entities=self.NUM_ALARM,
            aodh_edges=0)
        num_entities = self.num_default_entities + self.NUM_ALARM + \
            self.num_default_networks + self.num_default_ports
        num_edges = self.num_default_edges + self.num_default_ports

        # Test Assertions
        self._validate_graph_correctness(graph,
                                         num_entities,
                                         num_edges,
                                         entities)

    @staticmethod
    def _find_instance_resource_id():
        servers = TempestClients.nova().servers.list()
        return servers[0].id
