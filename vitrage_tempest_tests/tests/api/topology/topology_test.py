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

from vitrage_tempest_tests.tests.api.base import BaseVitrageTest
from vitrage_tempest_tests.tests.api.topology.utils \
    import TopologyHelper

LOG = logging.getLogger(__name__)


class BaseTopologyTest(BaseVitrageTest):
    """Topology test class for Vitrage API tests."""

    def setUp(self):
        super(BaseTopologyTest, self).setUp()
        self.topology_client = TopologyHelper()

    def test_compare_graphs(self):
        """Wrapper that returns a test graph."""
        api_graph = self.topology_client.get_api_topology('graph')
        cli_graph = self.topology_client.show_cli_topology()

        if self.topology_client.compare_graphs(api_graph, cli_graph) is False:
            LOG.error('The graph tempest_graph is not correct')
        else:
            LOG.info('The graph tempest_graph is correct')

    def test_get_tree_with_vms(self):
        """Wrapper that returns a test tree with created vm's"""
        resources = self.topology_client.create_machines(4)
        cli_graph = self.topology_client.show_cli_topology()

        if self.topology_client.validate_graph_correctness(
                cli_graph, resources) is False:
            LOG.error('The graph ' + self.name + ' is not correct')
        else:
            LOG.info('The graph ' + self.name + ' is correct')

    def test_get_graph_with_volume(self):
        """Wrapper that returns a test graph."""
        resources = self.topology_client.create_volume()
        cli_graph = self.topology_client.show_cli_topology()

        if self.topology_client.validate_graph_correctness(
                cli_graph, resources) is False:
            LOG.error('The graph ' + self.name + ' is not correct')
        else:
            LOG.info('The graph ' + self.name + ' is correct')
