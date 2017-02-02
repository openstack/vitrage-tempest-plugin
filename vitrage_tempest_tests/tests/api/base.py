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

import time

from oslo_log import log as logging
from oslotest import base

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.aodh import AODH_DATASOURCE
from vitrage.datasources.cinder.volume import CINDER_VOLUME_DATASOURCE
from vitrage.datasources.heat.stack import HEAT_STACK_DATASOURCE
from vitrage.datasources.neutron.network import NEUTRON_NETWORK_DATASOURCE
from vitrage.datasources.neutron.port import NEUTRON_PORT_DATASOURCE
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources import NOVA_ZONE_DATASOURCE
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.datasources.static_physical import SWITCH
from vitrage.graph.driver.networkx_graph import NXGraph
from vitrage.graph import Edge
from vitrage.graph import Vertex
from vitrage import keystone_client
from vitrage import os_clients
from vitrage import service
import vitrage_tempest_tests.tests.utils as utils
from vitrageclient import client as v_client

LOG = logging.getLogger(__name__)


class BaseApiTest(base.BaseTestCase):
    """Base test class for Vitrage API tests."""

    NUM_VERTICES_PER_TYPE = 'num_vertices'
    NUM_EDGES_PER_TYPE = 'num_edges_per_type'

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        super(BaseApiTest, cls).setUpClass()
        cls.conf = service.prepare_service([])

        cls.vitrage_client = \
            v_client.Client('1', session=keystone_client.get_session(cls.conf))
        cls.nova_client = cls._create_client(os_clients.nova_client, cls.conf)
        cls.cinder_client = cls._create_client(os_clients.cinder_client,
                                               cls.conf)
        cls.neutron_client = cls._create_client(os_clients.neutron_client,
                                                cls.conf)
        cls.heat_client = cls._create_client(os_clients.heat_client, cls.conf)

        cls.num_default_networks = \
            len(cls.neutron_client.list_networks()['networks'])
        cls.num_default_ports = \
            len(cls.neutron_client.list_ports()['ports'])
        cls.num_default_entities = 3
        cls.num_default_edges = 2

    @staticmethod
    def _create_client(client_func, conf):
        count = 0

        while count < 40:
            LOG.info("wait_for_client - " + client_func.func_name)
            client = client_func(conf)
            if client:
                return client
            count += 1
            time.sleep(5)

        LOG.info("wait_for_client - False")

        return None

    @staticmethod
    def _filter_list_by_pairs_parameters(origin_list,
                                         keys, values):
        filtered_list = []
        for item in origin_list:
            verification = 0
            for index in range(len(keys)):
                if utils.uni2str(item[keys[index]]) == values[index]:
                    verification += 1
                else:
                    break
            if verification == len(keys):
                filtered_list.append(item)
        return filtered_list

    def _create_volume_and_attach(self, name, size, instance_id, mount_point):
        volume = self.cinder_client.volumes.create(name=name,
                                                   size=size)
        time.sleep(2)
        self.cinder_client.volumes.attach(volume=volume,
                                          instance_uuid=instance_id,
                                          mountpoint=mount_point)

        self._wait_for_status(30,
                              self._check_num_volumes,
                              num_volumes=1,
                              state='in-use')

        time.sleep(2)

        return volume

    def _get_host(self):
        topology = self.vitrage_client.topology.get(all_tenants=1)
        host = filter(lambda item: item[VProps.TYPE] == NOVA_HOST_DATASOURCE,
                      topology['nodes'])
        return host[0]

    def _create_instances(self, num_instances, set_public_network=False):
        kwargs = {}
        flavors_list = self.nova_client.flavors.list()
        images_list = self.nova_client.images.list()
        if set_public_network:
            public_net = self._get_public_network()
            if public_net:
                kwargs.update({"networks": [{'uuid': public_net['id']}]})

        net = self.nova_client.networks.find(label="public")
        nics = [{'net-id': net.id}]
        resources = [self.nova_client.servers.create(
            name='%s-%s' % ('vm', index),
            flavor=flavors_list[0],
            image=images_list[0],
            nics=nics,
            **kwargs) for index in range(num_instances)]

        self._wait_for_status(30,
                              self._check_num_instances,
                              num_instances=num_instances,
                              state='active')
        time.sleep(2)

        return resources

    def _delete_instances(self):
        instances = self.nova_client.servers.list()
        for instance in instances:
            try:
                self.nova_client.servers.delete(instance)
            except Exception:
                pass

        self._wait_for_status(30,
                              self._check_num_instances,
                              num_instances=0)

        time.sleep(2)

    def _delete_volumes(self):
        volumes = self.cinder_client.volumes.list()
        for volume in volumes:
            try:
                self.cinder_client.volumes.detach(volume)
                self.cinder_client.volumes.force_delete(volume)
            except Exception:
                self.cinder_client.volumes.force_delete(volume)

        self._wait_for_status(30,
                              self._check_num_volumes,
                              num_volumes=0)

        time.sleep(2)

    def _check_num_instances(self, num_instances=0, state=''):
        if len(self.nova_client.servers.list()) != num_instances:
            return False

        return all(instance.__dict__['status'].upper() == state.upper()
                   for instance in self.nova_client.servers.list())

    def _check_num_volumes(self, num_volumes=0, state=''):
        if len(self.cinder_client.volumes.list()) != num_volumes:
            return False

        return all(volume.__dict__['status'].upper() == state.upper() and
                   len(volume.__dict__['attachments']) == 1
                   for volume in self.cinder_client.volumes.list())

    def _create_graph_from_graph_dictionary(self, api_graph):
        self.assertIsNotNone(api_graph)
        graph = NXGraph()

        nodes = api_graph['nodes']
        for i in range(len(nodes)):
            graph.add_vertex(Vertex(str(i), nodes[i]))

        edges = api_graph['links']
        for i in range(len(edges)):
            graph.add_edge(Edge(str(edges[i]['source']),
                                str(edges[i]['target']),
                                edges[i]['relationship_type']))

        return graph

    def _create_graph_from_tree_dictionary(self,
                                           api_graph,
                                           graph=None,
                                           ancestor=None):
        children = []
        graph = NXGraph() if not graph else graph

        if 'children' in api_graph:
            children = api_graph.copy()['children']
            del api_graph['children']

        vertex = Vertex(api_graph[VProps.VITRAGE_ID], api_graph)
        graph.add_vertex(vertex)
        if ancestor:
            graph.add_edge(Edge(ancestor[VProps.VITRAGE_ID],
                                vertex[VProps.VITRAGE_ID],
                                'label'))

        for entity in children:
            self._create_graph_from_tree_dictionary(entity, graph, vertex)

        return graph

    @staticmethod
    def _wait_for_status(max_waiting, func, **kwargs):
        count = 0
        while count < max_waiting:
            if func(**kwargs):
                return True
            count += 1
            time.sleep(2)
        LOG.info("wait_for_status - False")
        return False

    def _entities_validation_data(self, **kwargs):
        validation_data = []

        # openstack.cluster
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: OPENSTACK_CLUSTER,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('cluster_entities', 1),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('cluster_edges', 1)}
        validation_data.append(props)

        # nova.zone
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: NOVA_ZONE_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('zone_entities', 1),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('zone_edges', 2)}
        validation_data.append(props)

        # nova.host
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: NOVA_HOST_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('host_entities', 1),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('host_edges', 1)}
        validation_data.append(props)

        # nova.instance
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: NOVA_INSTANCE_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'instance_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'instance_edges', 0)}
        validation_data.append(props)

        # cinder.volume
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: CINDER_VOLUME_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'volume_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'volume_edges', 0)}
        validation_data.append(props)

        # switch
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: SWITCH,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'switch_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'switch_edges', 0)}
        validation_data.append(props)

        # aodh
        props = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: AODH_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'aodh_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'aodh_edges', 0)}
        validation_data.append(props)

        # neutron.network
        if kwargs.get('network_entities') is not None:
            props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                     VProps.TYPE: NEUTRON_NETWORK_DATASOURCE,
                     self.NUM_VERTICES_PER_TYPE: kwargs.get(
                         'network_entities', 0),
                     self.NUM_EDGES_PER_TYPE: kwargs.get(
                         'network_edges', 0)}
            validation_data.append(props)

        # neutron.port
        if kwargs.get('port_entities') is not None:
            props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                     VProps.TYPE: NEUTRON_PORT_DATASOURCE,
                     self.NUM_VERTICES_PER_TYPE: kwargs.get(
                         'port_entities', 0),
                     self.NUM_EDGES_PER_TYPE: kwargs.get(
                         'port_edges', 0)}
            validation_data.append(props)

        # heat.stack
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: HEAT_STACK_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'stack_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'stack_edges', 0)}
        validation_data.append(props)

        return validation_data

    def _validate_graph_correctness(self,
                                    graph,
                                    num_entities,
                                    num_edges,
                                    entities):
        self.assertIsNotNone(graph)
        self.assertIsNotNone(entities)

        for entity in entities:
            query = {
                VProps.CATEGORY: entity[VProps.CATEGORY],
                VProps.TYPE: entity[VProps.TYPE],
                VProps.IS_DELETED: False,
                VProps.IS_PLACEHOLDER: False
            }
            vertices = graph.get_vertices(vertex_attr_filter=query)
            self.assertEqual(entity[self.NUM_VERTICES_PER_TYPE],
                             len(vertices),
                             '%s%s' % ('Num vertices is incorrect for: ',
                                       entity[VProps.TYPE]))

            entity_num_edges = sum([len(graph.get_edges(vertex.vertex_id))
                                    for vertex in vertices])
            self.assertEqual(entity[self.NUM_EDGES_PER_TYPE],
                             entity_num_edges,
                             '%s%s' % ('Num edges is incorrect for: ',
                                       entity[VProps.TYPE]))

        self.assertEqual(num_entities, graph.num_vertices())
        self.assertEqual(num_edges, graph.num_edges())

    @staticmethod
    def _get_value(item, key):
        return utils.uni2str(item[key])

    def _get_public_network(self):
        networks = self.neutron_client.list_networks()
        public_nets = filter(
            lambda item: self._get_value(item, VProps.NAME) == 'public',
            networks['networks'])
        if not public_nets:
            return None
        return public_nets[0]
