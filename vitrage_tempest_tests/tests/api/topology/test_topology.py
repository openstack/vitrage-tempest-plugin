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

from oslo_log import log as logging

from vitrage_tempest_tests.tests.api.topology.base import BaseTopologyTest
import vitrage_tempest_tests.tests.utils as utils
from vitrageclient.exc import ClientException

LOG = logging.getLogger(__name__)
NOVA_QUERY = '{"and": [{"==": {"category": "RESOURCE"}},' \
             '{"==": {"is_deleted": false}},' \
             '{"==": {"is_placeholder": false}},' \
             '{"or": [{"==": {"type": "openstack.cluster"}},' \
             '{"==": {"type": "nova.instance"}},' \
             '{"==": {"type": "nova.host"}},' \
             '{"==": {"type": "nova.zone"}}]}]}'


class TestTopology(BaseTopologyTest):
    """Topology test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestTopology, cls).setUpClass()

    def test_compare_api_and_cli(self):
        """Wrapper that returns a test graph."""

        api_graph = self.vitrage_client.topology.get()
        cli_graph = utils.run_vitrage_command('vitrage topology show',
                                              self.conf)
        self._compare_graphs(api_graph, cli_graph)

    def test_default_graph(self):
        try:
            # create entities
            self._create_entities(num_instances=3, num_volumes=1)
            api_graph = self.vitrage_client.topology.get()
            self.assertIsNotNone(api_graph)
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=4,
                instance_entities=3, instance_edges=4,
                volume_entities=1, volume_edges=1)
            self._validate_graph_correctness(graph, 7, 6, entities)
        except Exception as e:
            LOG.exception(e)
        finally:
            self._rollback_to_default()

    def test_graph_with_query(self):
        try:
            # create entities
            self._create_entities(num_instances=3, num_volumes=1)
            api_graph = self.vitrage_client.topology.get(
                query=self._graph_query())
            self.assertIsNotNone(api_graph)
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=4,
                instance_entities=3, instance_edges=3)
            self._validate_graph_correctness(graph, 6, 5, entities)
        except Exception as e:
            LOG.exception(e)
        finally:
            self._rollback_to_default()

    def test_nova_tree(self):
        try:
            # create entities
            self._create_entities(num_instances=3, num_volumes=1)
            api_graph = self.vitrage_client.topology.get(graph_type='tree',
                                                         query=NOVA_QUERY)
            self.assertIsNotNone(api_graph)
            graph = self._create_graph_from_tree_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=4,
                instance_entities=3, instance_edges=3)
            self._validate_graph_correctness(graph, 6, 5, entities)
        except Exception as e:
            LOG.exception(e)
        finally:
            self._rollback_to_default()

    def test_tree_with_query(self):
        try:
            # create entities
            self._create_entities(num_instances=3)
            api_graph = self.vitrage_client.topology.get(
                graph_type='tree', query=self._tree_query())
            self.assertIsNotNone(api_graph)
            graph = self._create_graph_from_tree_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=1)
            self._validate_graph_correctness(graph, 3, 2, entities)
        except Exception as e:
            LOG.exception(e)
        finally:
            self._rollback_to_default()

    def test_tree_with_depth_exclude_instance(self):
        try:
            # create entities
            self._create_entities(num_instances=3)
            api_graph = self.vitrage_client.topology.get(
                limit=2, graph_type='tree', query=NOVA_QUERY)
            self.assertIsNotNone(api_graph)
            graph = self._create_graph_from_tree_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=1)
            self._validate_graph_correctness(graph, 3, 2, entities)
        finally:
            self._rollback_to_default()

    def test_tree_with_depth_include_instance(self):
        try:
            # create entities
            self._create_entities(num_instances=3)
            api_graph = self.vitrage_client.topology.get(
                limit=3, graph_type='tree', query=NOVA_QUERY)
            self.assertIsNotNone(api_graph)
            graph = self._create_graph_from_tree_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=4,
                instance_entities=3, instance_edges=3)
            self._validate_graph_correctness(graph, 6, 5, entities)
        finally:
            self._rollback_to_default()

    def test_graph_with_root_and_depth_exclude_instance(self):
        try:
            # create entities
            self._create_entities(num_instances=3)
            api_graph = self.vitrage_client.topology.get(
                limit=2, root="RESOURCE:openstack.cluster")
            self.assertIsNotNone(api_graph)
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=1)
            self._validate_graph_correctness(graph, 3, 2, entities)
        finally:
            self._rollback_to_default()

    def test_graph_with_root_and_depth_include_instance(self):
        try:
            # create entities
            self._create_entities(num_instances=3, num_volumes=1)
            api_graph = self.vitrage_client.topology.get(
                limit=4, root="RESOURCE:openstack.cluster")
            self.assertIsNotNone(api_graph)
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=4,
                instance_entities=3, instance_edges=4,
                volume_entities=1, volume_edges=1)
            self._validate_graph_correctness(graph, 7, 6, entities)
        finally:
            self._rollback_to_default()

    def test_graph_with_depth_and_no_root(self):
        try:
            # create entities
            self._create_entities(num_instances=3, num_volumes=1)
            self.vitrage_client.topology.get(limit=2)
        except ClientException as e:
            self.assertEqual(403, e.code)
            self.assertEqual(
                e.message,
                "Graph-type 'graph' requires a 'root' with 'depth'")
        finally:
            self._rollback_to_default()

    def test_graph_with_no_match_query(self):
        try:
            # create entities
            self._create_entities(num_instances=3, num_volumes=1)
            api_graph = self.vitrage_client.topology.get(
                query=self._graph_no_match_query())
            self.assertEqual(
                0,
                len(api_graph['nodes']), 'num of vertex node')
            self.assertEqual(
                0,
                len(api_graph['links']), 'num of edges')
        finally:
            self._rollback_to_default()

    def test_tree_with_no_match_query(self):
        try:
            # create entities
            self._create_entities(num_instances=3)
            api_graph = self.vitrage_client.topology.get(
                graph_type='tree', query=self._tree_no_match_query())
            self.assertEqual({}, api_graph)
        finally:
            self._rollback_to_default()
