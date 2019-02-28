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
from testtools import ExpectedException

from vitrage_tempest_plugin.tests.api.topology.base import BaseTopologyTest
from vitrage_tempest_plugin.tests.base import IsEmpty
import vitrage_tempest_plugin.tests.utils as utils
from vitrageclient.exceptions import ClientException

LOG = logging.getLogger(__name__)
NOVA_QUERY = '{"and": [{"==": {"vitrage_category": "RESOURCE"}},' \
             '{"==": {"vitrage_is_deleted": false}},' \
             '{"==": {"vitrage_is_placeholder": false}},' \
             '{"or": [{"==": {"vitrage_type": "openstack.cluster"}},' \
             '{"==": {"vitrage_type": "nova.instance"}},' \
             '{"==": {"vitrage_type": "nova.host"}},' \
             '{"==": {"vitrage_type": "nova.zone"}}]}]}'


class TestTopology(BaseTopologyTest):
    """Topology test class for Vitrage API tests."""

    NUM_INSTANCE = 3
    NUM_VOLUME = 1

    def tearDown(self):
        super(TestTopology, self).tearDown()
        self._rollback_to_default()

    @utils.tempest_logger
    def test_compare_api_and_cli(self):
        """compare_api_and_cli

        This test validate correctness of topology graph:
         cli via api
        """
        api_graph = self.vitrage_client.topology.get(all_tenants=True)
        cli_graph = utils.run_vitrage_command(
            'vitrage topology show --all-tenants')

        self._assert_graph_equal(api_graph, json.loads(cli_graph))

    @utils.tempest_logger
    def test_default_graph_all_tenants(self):
        """default_graph

        This test validate correctness of default topology graph, using the
        --all-tenants option.
        """
        self._do_test_default_graph(
            num_default_networks=self.num_default_networks, all_tenants=True)

    @utils.tempest_logger
    def test_default_graph(self):
        """default_graph

        This test validate correctness of default topology graph, not using the
        --all-tenants option. Since the tenant of all entities in the graph is
        either admin or None, this test is expected to be identical to the one
        with --all-tenants
        """
        num_admin_networks = self._calc_num_admin_tenant_networks()

        self._do_test_default_graph(num_default_networks=num_admin_networks,
                                    all_tenants=False)

    @utils.tempest_logger
    def test_default_graph_for_tenant(self):
        """default_graph

        This test validate correctness of default topology graph when queried
        by another tenant.
        """
        # Action - create entities as the default tenant
        self._create_entities(num_instances=self.NUM_INSTANCE,
                              num_volumes=self.NUM_VOLUME)

        # Calculate expected results for another tenant - the other tenant
        # should not see instances and volumes of the default tenant.
        # All it can see is its private network.
        tenant_client = self.vitrage_client_for_demo_user
        api_graph = tenant_client.topology.get(all_tenants=False)
        graph = self._create_graph_from_graph_dictionary(api_graph)

        entities = self._entities_validation_data(
            cluster_entities=0, cluster_edges=0, zone_entities=0,
            zone_edges=0, host_entities=0, host_edges=0,
            instance_entities=0, instance_edges=0, volume_entities=0,
            volume_edges=0)
        num_entities = self._calc_num_tenant_networks()

        # Test Assertions
        self._validate_graph_correctness(graph, num_entities, 0, entities)

    @utils.tempest_logger
    def test_graph_with_query(self):
        """graph_with_query

        This test validate correctness of topology graph
        with query
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE,
                              num_volumes=self.NUM_VOLUME)

        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(
            query=self._graph_query(),
            all_tenants=True)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1,
            host_edges=self.NUM_INSTANCE + 1,
            instance_entities=self.NUM_INSTANCE,
            instance_edges=self.NUM_INSTANCE)
        num_entities = self.num_default_entities + self.NUM_INSTANCE
        num_edges = self.num_default_edges + self.NUM_INSTANCE

        # Test Assertions
        self._validate_graph_correctness(graph,
                                         num_entities,
                                         num_edges,
                                         entities)

    @utils.tempest_logger
    def test_graph_with_query_for_tenant(self):
        """graph_with_query

        This test validate correctness of topology graph
        with query, when queried by another tenant.
        """
        # Action - create entities as the default tenant
        self._create_entities(num_instances=self.NUM_INSTANCE,
                              num_volumes=self.NUM_VOLUME)

        # Calculate expected results - the other tenant should not see
        # instances and volumes of the default tenant
        tenant_client = self.vitrage_client_for_demo_user
        api_graph = tenant_client.topology.get(query=self._graph_query())
        graph = self._create_graph_from_graph_dictionary(api_graph)

        entities = self._entities_validation_data(
            cluster_entities=0, cluster_edges=0, zone_entities=0,
            zone_edges=0, host_entities=0, host_edges=0,
            instance_entities=0, instance_edges=0, volume_entities=0,
            volume_edges=0)

        # Test Assertions
        self._validate_graph_correctness(graph, 0, 0, entities)

    @utils.tempest_logger
    def test_nova_tree(self):
        """nova_tree

        This test validate correctness of topology tree
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE,
                              num_volumes=self.NUM_VOLUME)

        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(
            graph_type='tree', query=NOVA_QUERY, all_tenants=True)
        graph = self._create_graph_from_tree_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1,
            host_edges=self.NUM_INSTANCE + 1,
            instance_entities=self.NUM_INSTANCE,
            instance_edges=self.NUM_INSTANCE)
        num_entities = self.num_default_entities + self.NUM_INSTANCE
        num_edges = self.num_default_edges + self.NUM_INSTANCE

        # Test Assertions
        self._validate_graph_correctness(graph,
                                         num_entities,
                                         num_edges,
                                         entities)

    @utils.tempest_logger
    def test_tree_with_query(self):
        """tree_with_query

        This test validate correctness of topology tree
        with query
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE)

        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(
            graph_type='tree', query=self._tree_query(), all_tenants=True)
        graph = self._create_graph_from_tree_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1, host_edges=1)

        # Test Assertions
        self._validate_graph_correctness(graph,
                                         self.num_default_entities,
                                         self.num_default_edges,
                                         entities)

    @utils.tempest_logger
    def test_tree_with_depth_exclude_instance(self):
        """tree_with_query

        This test validate correctness of topology tree
        with query
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE)

        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(
            limit=2, graph_type='tree', query=NOVA_QUERY, all_tenants=True)
        graph = self._create_graph_from_tree_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1, host_edges=1)

        # Test Assertions
        self._validate_graph_correctness(graph,
                                         self.num_default_entities,
                                         self.num_default_edges,
                                         entities)

    @utils.tempest_logger
    def test_tree_with_depth_include_instance(self):
        """tree_with_query

        This test validate correctness of topology tree
        with query
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE)

        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(
            limit=3, graph_type='tree', query=NOVA_QUERY, all_tenants=True)
        graph = self._create_graph_from_tree_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1,
            host_edges=self.NUM_INSTANCE + 1,
            instance_entities=self.NUM_INSTANCE,
            instance_edges=self.NUM_INSTANCE)
        num_entities = self.num_default_entities + self.NUM_INSTANCE
        num_edges = self.num_default_edges + self.NUM_INSTANCE

        # Test Assertions
        self._validate_graph_correctness(graph,
                                         num_entities,
                                         num_edges,
                                         entities)

    @utils.tempest_logger
    def test_graph_with_depth_and_no_root(self):
        """graph_with_depth_and_no_root

        This test validate correctness of topology
        graph with depth and without root
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE,
                              num_volumes=self.NUM_VOLUME)

        with ExpectedException(ClientException,
                               "Graph-type 'graph' "
                               "requires a 'root' with 'depth'"):

            self.vitrage_client.topology.get(
                limit=2,
                root=None,
                all_tenants=True)

    @utils.tempest_logger
    def test_graph_with_no_match_query(self):
        """graph_with_no_match_query

        This test validate correctness of topology graph
        with no match query
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE,
                              num_volumes=self.NUM_VOLUME)

        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(
            query=self._graph_no_match_query(), all_tenants=True)

        # Test Assertions
        self.assertThat(api_graph['nodes'],
                        IsEmpty(), 'num of vertex node')
        self.assertThat(api_graph['links'], IsEmpty(), 'num of edges')

    @utils.tempest_logger
    def test_tree_with_no_match_query(self):
        """tree_with_no_match_query

        This test validate correctness of topology tree
        with no match query
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE)

        # Calculate expected results
        api_graph = self.vitrage_client.topology.get(
            graph_type='tree',
            query=self._tree_no_match_query(),
            all_tenants=True)

        # Test Assertions
        self.assert_is_empty(api_graph)

    @utils.tempest_logger
    def _do_test_default_graph(self, num_default_networks, all_tenants):
        """default_graph

        This test validate correctness of default topology graph
        """
        # Action
        self._create_entities(num_instances=self.NUM_INSTANCE,
                              num_volumes=self.NUM_VOLUME)

        # Calculate expected results
        api_graph = \
            self.vitrage_client.topology.get(all_tenants=all_tenants)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data(
            host_entities=1,
            host_edges=self.NUM_INSTANCE + 1,
            instance_entities=self.NUM_INSTANCE,
            instance_edges=2 * self.NUM_INSTANCE + self.NUM_VOLUME,
            volume_entities=self.NUM_VOLUME,
            volume_edges=self.NUM_VOLUME)
        num_entities = self.num_default_entities + self.NUM_VOLUME + \
            2 * self.NUM_INSTANCE + num_default_networks + \
            self.num_default_ports
        num_edges = self.num_default_edges + 3 * self.NUM_INSTANCE + \
            self.NUM_VOLUME + self.num_default_ports

        # Test Assertions
        self._validate_graph_correctness(graph,
                                         num_entities,
                                         num_edges,
                                         entities)
