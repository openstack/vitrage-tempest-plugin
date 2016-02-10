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

import os

import oslo_messaging

from oslo_config import cfg
from oslo_log import log as logging
from vitrage.api.controllers.v1.topology import TopologyController
from vitrage_tempest_tests.tests.api.base import BaseVitrageTest
from vitrage_tempest_tests.tests.base_mock import BaseMock

LOG = logging.getLogger(__name__)


class BaseTopologyTest(BaseVitrageTest):
    """Topology test class for Vitrage API tests."""

    def __init__(self, *args, **kwds):
        super(BaseTopologyTest, self).__init__(*args, **kwds)
        self.created_graphs = []
        self.name = 'tempest_graph'
        self.depth = ''
        self.query = ''
        self.root = ''

        """ Get client """
        transport = oslo_messaging.get_transport(cfg.CONF)
        cfg.CONF.set_override('rpc_backend', 'rabbit')
        target = oslo_messaging.Target(topic='rpcapiv1')
        self.client = oslo_messaging.RPCClient(transport, target)

    def test_get_graph(self):
        """Wrapper that returns a test graph."""
        self.graph_type = 'graph'
        self.graph = self._get_topology()
        self._validate_graph_correctness()
        LOG.debug('The graph ' + self.name + ' does not exist')

    def test_get_tree(self):
        """Wrapper that returns a test tree."""
        self.graph_type = 'tree'
        self.graph = self._get_topology()
        self._validate_graph_correctness()
        LOG.debug('The graph tree ' + self.name + ' exist')

    def _get_topology(self):
        """Get Graph objects returned by the v1 client """
        try:
            g = TopologyController().get_graph(graph_type=self.graph_type)

        except Exception as e:
            LOG.exception("Failed to get topology (graph_type = " +
                          self.graph_type + ") %s ", e)
            return None

        return g

    def _validate_graph_correctness(self):
        """Compare Graph object to graph form os terminal """

        print("The topology graph taken by api is : %s", self.graph)

    def _create_graph_by_mock(self):
        """Create MOCK Graph and copied to the string """
        processor = BaseMock.create_processor_with_graph(self)
        entity_graph = processor.entity_graph
        a = entity_graph.output_graph()
        print (a)

    @staticmethod
    def _show_topology():
        text_out = os.popen("vitrage topology show").read()
        print (text_out)

        if "RESOURCE" not in text_out:
            LOG.info('The topology graph does not exist')
            return False
        else:
            LOG.info('The topology graph exist')
            return True
