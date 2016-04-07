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
import vitrage_tempest_tests.tests.utils as utils

from oslo_log import log as logging

from vitrage.api.controllers.v1.topology import TopologyController
from vitrage.common.constants import VertexProperties as VProps
from vitrage_tempest_tests.tests.api.base import BaseVitrageTest

LOG = logging.getLogger(__name__)


class TopologyHelper(BaseVitrageTest):
    """Topology test class for Vitrage API tests."""

    def __init__(self):
        super(TopologyHelper, self).__init__()
        self.client = utils.get_client()
        self.depth = ''
        self.query = ''
        self.root = ''

    def get_api_topology(self, graph_type):
        """Get Graph objects returned by the v1 client """
        try:
            api_graph = TopologyController().get_graph(graph_type=graph_type,
                                                       depth=self.depth,
                                                       query=self.query,
                                                       root=self.root)
        except Exception as e:
            LOG.exception("Failed to get topology (graph_type = " +
                          graph_type + ") %s ", e)
            return None

        return api_graph

    def show_cli_topology(self):
        """Get Graph objects returned by cli """
        LOG.debug("The command is : vitrage topology show")

        return utils.run_vitrage_command_with_user(
            "vitrage topology show", self.conf.service_credentials.user)

    def create_volume(self):
        flavor_id = self.get_flavor_id_from_list()
        image_id = self.get_image_id_from_list()

        resources = ["vm_for_vol", "vol_for_vm"]
        self.create_vm_with_exist_image(resources[0], flavor_id, image_id)
        self.create_volume_with_exist_size(resources[1])
        self.attach_volume(resources[0], resources[1])
        return resources

    @staticmethod
    def compare_graphs(api_graph, cli_graph):
        """Compare Graph object to graph form terminal """
        if not api_graph:
            LOG.error("The topology graph taken from rest api is empty")
            return False
        if not cli_graph:
            LOG.error("The topology graph taken from terminal is empty")
            return False

        parsed_topology = json.loads(cli_graph)
        LOG.debug("The topology graph taken from terminal is : " +
                  json.dumps(parsed_topology))
        LOG.debug("The topology graph taken by api is : %s",
                  json.dumps(api_graph))

        cli_items = sorted(parsed_topology.items())
        api_items = sorted(api_graph.items())

        for item in cli_items[4][1]:
            item.pop(VProps.UPDATE_TIMESTAMP, None)

        for item in api_items[4][1]:
            item.pop(VProps.UPDATE_TIMESTAMP, None)

        return cli_items == api_items

    @staticmethod
    def validate_graph_correctness(cli_graph, resources):
        """Compare Graph object to graph form terminal """
        if not cli_graph:
            LOG.error("The topology graph taken from terminal is empty")
            return False
        if not resources:
            LOG.error("The resources list is empty")
            return False

        parsed_topology = json.loads(cli_graph)
        LOG.debug("The topology graph taken from terminal is : " +
                  json.dumps(parsed_topology))
        cli_items = sorted(parsed_topology.items())

        for resource_name in resources:
            for item in cli_items[4][1]:
                item.pop(VProps.UPDATE_TIMESTAMP, None)
                if resource_name not in cli_items[4][1]:
                    LOG.error("The resources " + resource_name +
                              "doesn't exist in the topology graph")
                    return False
        return True
