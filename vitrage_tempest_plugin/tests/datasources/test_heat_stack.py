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

from oslo_log import log as logging
from vitrage_tempest_plugin.tests import utils

from vitrage_tempest_plugin.tests.api.topology.base import BaseTopologyTest
from vitrage_tempest_plugin.tests.common.general_utils\
    import tempest_resources_dir
from vitrage_tempest_plugin.tests.common import heat_utils

LOG = logging.getLogger(__name__)


class TestHeatStack(BaseTopologyTest):
    NUM_STACKS = 1

    def setUp(self):
        super(TestHeatStack, self).setUp()

    def tearDown(self):
        super(TestHeatStack, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestHeatStack, cls).setUpClass()

    @utils.tempest_logger
    def test_nested_heat_stack(self):
        self._test_heat_stack(nested=True,
                              tmpl_file='heat_nested_template.yaml')

    @utils.tempest_logger
    def test_heat_stack(self):
        self._test_heat_stack(nested=False, tmpl_file='heat_template.yaml')

    def _test_heat_stack(self, nested, tmpl_file):
        """heat stack test

        This test validate correctness topology graph with heat stack module
        """
        template_file = tempest_resources_dir() + '/heat/' + tmpl_file
        try:
            # Action
            heat_utils.create_stacks(self.NUM_STACKS, nested, template_file)

            # Calculate expected results
            api_graph = self.vitrage_client.topology.get(all_tenants=True)
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1,
                host_edges=1 + self.NUM_STACKS,
                instance_entities=self.NUM_STACKS,
                instance_edges=3 * self.NUM_STACKS,
                network_entities=self.num_default_networks,
                network_edges=self.num_default_ports + self.NUM_STACKS,
                port_entities=self.num_default_ports + self.NUM_STACKS,
                port_edges=self.num_default_ports + 2 * self.NUM_STACKS,
                stack_entities=self.NUM_STACKS,
                stack_edges=self.NUM_STACKS)
            num_entities = self.num_default_entities + 3 * self.NUM_STACKS + \
                self.num_default_networks + self.num_default_ports
            num_edges = self.num_default_edges + 4 * self.NUM_STACKS + \
                self.num_default_ports

            # Test Assertions
            self._validate_graph_correctness(graph,
                                             num_entities,
                                             num_edges,
                                             entities)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            heat_utils.delete_all_stacks()
