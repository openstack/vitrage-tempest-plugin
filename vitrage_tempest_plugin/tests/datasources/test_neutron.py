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

from vitrage.common.constants import VertexProperties as VProps
from vitrage_tempest_plugin.tests.api.topology.base import BaseTopologyTest
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common import nova_utils
from vitrage_tempest_plugin.tests import utils

LOG = logging.getLogger(__name__)


class TestNeutron(BaseTopologyTest):
    NUM_INSTANCE = 3

    def setUp(self):
        super(TestNeutron, self).setUp()

    def tearDown(self):
        super(TestNeutron, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestNeutron, cls).setUpClass()

    @utils.tempest_logger
    def test_neutron(self):
        """neutron test

        This test validate correctness topology graph with neutron module
        """

        try:
            # Action
            nova_utils.create_instances(num_instances=self.NUM_INSTANCE,
                                        set_public_network=True)

            # Calculate expected results
            api_graph = self.vitrage_client.topology.get(all_tenants=True)
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1,
                host_edges=1 + self.NUM_INSTANCE,
                instance_entities=self.NUM_INSTANCE,
                instance_edges=2 * self.NUM_INSTANCE,
                network_entities=self.num_default_networks,
                network_edges=self.num_default_ports + self.NUM_INSTANCE,
                port_entities=self.num_default_ports + self.NUM_INSTANCE,
                port_edges=self.num_default_ports + 2 * self.NUM_INSTANCE)
            num_entities = self.num_default_entities + \
                2 * self.NUM_INSTANCE + \
                self.num_default_networks + self.num_default_ports
            num_edges = self.num_default_edges + 3 * self.NUM_INSTANCE + \
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
            nova_utils.delete_all_instances()

    @staticmethod
    def _get_network_name(instance, networks):
        for network in networks:
            try:
                if len(instance.networks[network[VProps.NAME]]) > 0:
                    return network[VProps.NAME]
            except Exception:
                pass
        return None

    @staticmethod
    def _port_to_inst_edges(instances, network_name, ports):
        counter = 0
        for vm in instances:
            for port in ports:
                ips_number = 0
                for vm_ip in vm.addresses[network_name]:
                    for port_ip in port['fixed_ips']:
                        if vm_ip['addr'] == port_ip['ip_address']:
                            ips_number += 1
                            break
                if ips_number == len(vm.addresses[network_name]):
                    counter += 1
                    break
        return counter

    def _port_to_network_edges(self, networks, ports):
        counter = 0
        for net in networks:
            counter += len(g_utils.all_matches(ports, network_id=net['id']))
        return counter
