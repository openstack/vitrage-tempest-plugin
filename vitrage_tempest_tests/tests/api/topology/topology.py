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
import subprocess
import vitrage_tempest_tests.tests.utils as utils

from oslo_log import log as logging

from vitrage.api.controllers.v1.topology import TopologyController
from vitrage.common.constants import VertexProperties as VProps
from vitrage_tempest_tests.tests.api.base import BaseVitrageTest

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
        self._get_env_params()
        self.client = utils.get_client()

    def test_get_tree(self):
        """Wrapper that returns a test tree."""
        self._get_topology('tree')

    def test_get_graph(self):
        """Wrapper that returns a test graph."""
        self._get_topology('graph')

        if self._validate_graph_correctness() is False:
            LOG.error('The graph ' + self.name + ' is not correct')
        else:
            LOG.info('The graph ' + self.name + ' is correct')

    def _get_topology(self, graph_type):
        """Get Graph objects returned by the v1 client """
        try:
            g = TopologyController().get_graph(graph_type=graph_type,
                                               depth=self.depth,
                                               query=self.query,
                                               root=self.root)
        except Exception as e:
            LOG.exception("Failed to get topology (graph_type = " +
                          self.graph_type + ") %s ", e)
            return None

        return g

    def _validate_graph_correctness(self):
        """Compare Graph object to graph form terminal """
        cli_graph = self._show_topology()
        if cli_graph == '':
            LOG.error("The topology graph taken from terminal is empty")
            return False

        parsed_topology = json.loads(cli_graph)
        LOG.debug("The topology graph taken from terminal is : " +
                  json.dumps(parsed_topology))
        LOG.debug("The topology graph taken by api is : %s",
                  json.dumps(self.graph))

        cli_items = sorted(parsed_topology.items())
        api_items = sorted(self.graph.items())

        for item in cli_items[4][1]:
            item.pop(VProps.UPDATE_TIMESTAMP, None)

        for item in api_items[4][1]:
            item.pop(VProps.UPDATE_TIMESTAMP, None)

        return cli_items == api_items

    def _show_topology(self):
        LOG.debug("The command is : vitrage topology show")
        p = subprocess.Popen("cd /home/stack/devstack; . openrc " +
                             self.user + " " + self.tenant_user +
                             "; vitrage topology show",
                             shell=True,
                             executable="/bin/bash",
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if stderr != '':
            LOG.error("The command output error is : " + stderr)
        if stdout != '':
            LOG.debug("The command output is : \n" + stdout)
            return stdout
        return None

    def _get_env_params(self):
        conf = utils.get_conf()
        self.user = conf.keystone_authtoken.admin_user
        self.tenant_user = conf.keystone_authtoken.admin_tenant_name
