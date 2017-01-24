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

import time
import traceback

from oslo_log import log as logging
from vitrage_tempest_tests.tests import utils

from vitrage_tempest_tests.tests.api.topology.base import BaseTopologyTest

LOG = logging.getLogger(__name__)


class TestHeatStack(BaseTopologyTest):
    NUM_STACKS = 1

    @classmethod
    def setUpClass(cls):
        super(TestHeatStack, cls).setUpClass()

    @utils.tempest_logger
    def test_heat_stack(self):
        """heat stack test

        This test validate correctness topology graph with heat stack module
        """

        try:
            # Action
            self._create_stacks(num_stacks=self.NUM_STACKS)

            # Calculate expected results
            api_graph = self.vitrage_client.topology.get(all_tenants=1)
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
            traceback.print_exc()
            LOG.exception(e)
            raise
        finally:
            self._delete_stacks()

    def _create_stacks(self, num_stacks):
        with open('/etc/vitrage/heat_template.yaml', 'rb') as f:
            template_data = f.read()

        for i in range(num_stacks):
            self.heat_client.stacks.create(stack_name='stack_%s' % i,
                                           template=template_data,
                                           parameters={})
        self._wait_for_status(45,
                              self._check_num_stacks,
                              num_stacks=num_stacks,
                              state='CREATE_COMPLETE')

        time.sleep(2)

    def _delete_stacks(self):
        stacks = self.heat_client.stacks.list()
        for stack in stacks:
            try:
                self.heat_client.stacks.delete(stack.__dict__['id'])
            except Exception:
                pass

        self._wait_for_status(30,
                              self._check_num_stacks,
                              num_stacks=0)

        time.sleep(2)

    def _check_num_stacks(self, num_stacks, state=''):
        stacks_list = \
            [stack.__dict__ for stack in self.heat_client.stacks.list()
             if 'FAILED' not in stack.__dict__['stack_status']]
        if len(stacks_list) != num_stacks:
            return False

        return all(stack['stack_status'].upper() == state.upper()
                   for stack in stacks_list)
