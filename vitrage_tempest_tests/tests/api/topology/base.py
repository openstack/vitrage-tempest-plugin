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
import time

from oslo_log import log as logging

from vitrage.common.constants import VertexProperties as VProps
from vitrage_tempest_tests.tests.api.base import BaseApiTest


LOG = logging.getLogger(__name__)


class BaseTopologyTest(BaseApiTest):
    """Topology test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseTopologyTest, cls).setUpClass()

    def _rollback_to_default(self):
        self._delete_entities()
        api_graph = self.vitrage_client.topology.get(
            limit=4,
            root='RESOURCE:openstack.cluster:OpenStack Cluster',
            all_tenants=1)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data()
        num_default_entities = self.num_default_entities + \
            self.num_default_networks + self.num_default_ports
        num_default_edges = self.num_default_edges + self.num_default_ports
        self._validate_graph_correctness(graph,
                                         num_default_entities,
                                         num_default_edges,
                                         entities)

    def _create_entities(self, num_instances=0, num_volumes=0, end_sleep=3):
        if num_instances > 0:
            resources = self._create_instances(num_instances)

        self.assertNotEqual(len(resources), 0, 'The instances list is empty')
        if num_volumes > 0:
            self._create_volume_and_attach('volume-1', 1,
                                           resources[0].id,
                                           '/tmp/vda')

        # waiting until all the entities creation were processed by the
        # entity graph processor
        time.sleep(end_sleep)

    def _delete_entities(self):
        self._delete_volumes()
        self._delete_instances()

        # waiting until all the entities deletion were processed by the
        # entity graph processor
        time.sleep(2)

    def _compare_graphs(self, api_graph, cli_graph):
        """Compare Graph object to graph form terminal """
        self.assertNotEqual(len(api_graph), 0,
                            'The topology graph taken from rest api is empty')
        self.assertNotEqual(len(cli_graph), 0,
                            'The topology graph taken from terminal is empty')

        parsed_topology = json.loads(cli_graph)

        sorted_cli_graph = sorted(parsed_topology.items())
        sorted_api_graph = sorted(api_graph.items())

        for item in sorted_cli_graph[4][1]:
            item.pop(VProps.UPDATE_TIMESTAMP, None)

        for item in sorted_api_graph[4][1]:
            item.pop(VProps.UPDATE_TIMESTAMP, None)

        for item in sorted_cli_graph[4][1]:
            item.pop(VProps.SAMPLE_TIMESTAMP, None)

        for item in sorted_api_graph[4][1]:
            item.pop(VProps.SAMPLE_TIMESTAMP, None)

        self.assertEqual(sorted_cli_graph, sorted_api_graph)

    @staticmethod
    def _graph_query():
        return '{"and": [{"==": {"category": "RESOURCE"}},' \
               '{"==": {"is_deleted": false}},' \
               '{"==": {"is_placeholder": false}},' \
               '{"or": [{"==": {"type": "openstack.cluster"}},' \
               '{"==": {"type": "nova.instance"}},' \
               '{"==": {"type": "nova.host"}},' \
               '{"==": {"type": "nova.zone"}}]}]}'

    @staticmethod
    def _tree_query():
        return '{"and": [{"==": {"category": "RESOURCE"}},' \
               '{"==": {"is_deleted": false}},' \
               '{"==": {"is_placeholder": false}},' \
               '{"or": [{"==": {"type": "openstack.cluster"}},' \
               '{"==": {"type": "nova.host"}},' \
               '{"==": {"type": "nova.zone"}}]}]}'

    @staticmethod
    def _graph_no_match_query():
        return '{"and": [{"==": {"category": "test"}},' \
               '{"==": {"is_deleted": false}},' \
               '{"==": {"is_placeholder": false}},' \
               '{"or": [{"==": {"type": "openstack.cluster"}},' \
               '{"==": {"type": "nova.instance"}},' \
               '{"==": {"type": "nova.host"}},' \
               '{"==": {"type": "nova.zone"}}]}]}'

    @staticmethod
    def _tree_no_match_query():
        return '{"and": [{"==": {"category": "test"}},' \
               '{"==": {"is_deleted": false}},' \
               '{"==": {"is_placeholder": false}},' \
               '{"or": [{"==": {"type": "openstack.cluster"}},' \
               '{"==": {"type": "nova.host"}},' \
               '{"==": {"type": "nova.zone"}}]}]}'
