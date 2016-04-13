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
        api_graph = self.vitrage_client.topology.get()
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data()
        self._validate_graph_correctness(graph, 3, 2, entities)

    def _create_entities(self, num_instances=0, num_volumes=0, end_sleep=3):
        if num_instances > 0:
            resources = self._create_instances(num_instances)

        if num_volumes > 0:
            self._create_volume_and_attach('volume-1', 1,
                                           resources[0].__dict__['id'],
                                           '/tmp/vda')
        # waiting until all the entities creation were processed by the
        # entity graph processor
        time.sleep(end_sleep)

    def _delete_entities(self):
        self._delete_volumes()
        self._delete_instances()

        # waiting until all the entities deletion were processed by the
        # entity graph processor
        time.sleep(5)

    @staticmethod
    def _compare_graphs(api_graph, cli_graph):
        """Compare Graph object to graph form terminal """
        if not api_graph:
            LOG.error("The topology graph taken from rest api is empty")
            return False
        if not cli_graph:
            LOG.error("The topology graph taken from terminal is empty")
            return False

        parsed_topology = json.loads(cli_graph)

        sorted_cli_graph = sorted(parsed_topology.items())
        sorted_api_graph = sorted(api_graph.items())

        for item in sorted_cli_graph[4][1]:
            item.pop(VProps.UPDATE_TIMESTAMP, None)

        for item in sorted_api_graph[4][1]:
            item.pop(VProps.UPDATE_TIMESTAMP, None)

        return sorted_cli_graph == sorted_api_graph

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
