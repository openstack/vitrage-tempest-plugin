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
import os
import os.path
import time

from oslo_log import log as logging
from tempest import test

from vitrage import clients
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources import CINDER_VOLUME_DATASOURCE
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage.datasources import NOVA_ZONE_DATASOURCE
from vitrage.datasources import OPENSTACK_CLUSTER
from vitrage.datasources.static_physical import SWITCH
from vitrage.graph import Edge
from vitrage.graph import NXGraph
from vitrage.graph import Vertex
from vitrage import keystone_client
from vitrage import service
from vitrage_tempest_tests.tests import OPTS
from vitrageclient import client as v_client

LOG = logging.getLogger(__name__)


class BaseTopologyTest(test.BaseTestCase):
    """Topology test class for Vitrage API tests."""

    NUM_ENTITIES_PER_TYPE = 'num_vertices'
    NUM_EDGES_PER_TYPE = 'num_edges_per_type'

    @classmethod
    def setUpClass(cls):
        super(BaseTopologyTest, cls).setUpClass()
        cls.conf = service.prepare_service([])
        cls.conf.register_opts(list(OPTS), group='keystone_authtoken')
        cls.vitrage_client = \
            v_client.Client('1', session=keystone_client.get_session(cls.conf))
        cls.nova_client = clients.nova_client(cls.conf)
        cls.cinder_client = clients.cinder_client(cls.conf)

    def _rollback_to_default(self):
        self._delete_entities(instance=True, volume=True, static_physical=True)
        api_graph = self.vitrage_client.topology.get()
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data()
        self._validate_graph_correctness(graph, 3, 2, entities)

    def _create_entities(self, num_instances=0, num_volumes=0, end_sleep=3):
        if num_instances > 0:
            resources = self._create_instances(num_instances)
            self._wait_for_status(20,
                                  self._check_num_instances,
                                  num_instances=num_instances)
            time.sleep(1)

        if num_volumes > 0:
            self._create_volume_and_attach('volume-1', 1,
                                           resources[0].__dict__['id'],
                                           '/tmp/vda')
            self._wait_for_status(20,
                                  self._check_num_volumes,
                                  num_volumes=1)

        # waiting until all the entities creation were processed by the
        # entity graph processor
        time.sleep(end_sleep)

    def _delete_entities(self,
                         instance=False,
                         volume=False,
                         static_physical=False):
        if volume:
            self._delete_volumes()
            self._wait_for_status(30,
                                  self._check_num_volumes,
                                  num_volumes=0)

        if instance:
            self._delete_instances()
            self._wait_for_status(20,
                                  self._check_num_instances,
                                  num_instances=0)

        if static_physical:
            self._delete_switches()
            time.sleep(2)

        # waiting until all the entities deletion were processed by the
        # entity graph processor
        time.sleep(5)

    def _delete_switches(self):
        path = '/etc/vitrage/static_datasources/tempest_configuration.yaml'
        if os.path.exists(path):
            os.remove(path)

    def _entities_validation_data(self, cluster_entities=1, cluster_edges=1,
                                  zone_entities=1, zone_edges=2,
                                  host_entities=1, host_edges=1,
                                  instance_entities=0, instance_edges=0,
                                  volume_entities=0, volume_edges=0,
                                  switch_entities=0, switch_edges=0):
        return [
            {VProps.TYPE: OPENSTACK_CLUSTER,
             self.NUM_ENTITIES_PER_TYPE: cluster_entities,
             self.NUM_EDGES_PER_TYPE: cluster_edges},
            {VProps.TYPE: NOVA_ZONE_DATASOURCE,
             self.NUM_ENTITIES_PER_TYPE: zone_entities,
             self.NUM_EDGES_PER_TYPE: zone_edges},
            {VProps.TYPE: NOVA_HOST_DATASOURCE,
             self.NUM_ENTITIES_PER_TYPE: host_entities,
             self.NUM_EDGES_PER_TYPE: host_edges},
            {VProps.TYPE: NOVA_INSTANCE_DATASOURCE,
             self.NUM_ENTITIES_PER_TYPE: instance_entities,
             self.NUM_EDGES_PER_TYPE: instance_edges},
            {VProps.TYPE: CINDER_VOLUME_DATASOURCE,
             self.NUM_ENTITIES_PER_TYPE: volume_entities,
             self.NUM_EDGES_PER_TYPE: volume_edges},
            {VProps.TYPE: SWITCH,
             self.NUM_ENTITIES_PER_TYPE: switch_entities,
             self.NUM_EDGES_PER_TYPE: switch_edges}
        ]

    def _validate_graph_correctness(self,
                                    graph,
                                    num_entities,
                                    num_edges,
                                    entities):
        self.assertIsNot(None, graph)
        self.assertIsNot(None, entities)
        self.assertEqual(num_entities, graph.num_vertices())
        self.assertEqual(num_edges, graph.num_edges())

        for entity in entities:
            query = {
                VProps.CATEGORY: EntityCategory.RESOURCE,
                VProps.TYPE: entity[VProps.TYPE],
                VProps.IS_DELETED: False,
                VProps.IS_PLACEHOLDER: False
            }
            vertices = graph.get_vertices(vertex_attr_filter=query)
            self.assertEqual(entity[self.NUM_ENTITIES_PER_TYPE], len(vertices))

            num_edges = sum([len(graph.get_edges(vertex.vertex_id))
                             for vertex in vertices])
            self.assertEqual(entity[self.NUM_EDGES_PER_TYPE], num_edges)

    def _check_num_instances(self, num_instances=0):
        return len(self.nova_client.servers.list()) == num_instances

    def _check_num_volumes(self, num_volumes=0):
        return len(self.cinder_client.volumes.list()) == num_volumes

    def _create_volume_and_attach(self, name, size, instance_id, mount_point):
        volume = self.cinder_client.volumes.create(display_name=name,
                                                   size=size)
        time.sleep(3)
        self.cinder_client.volumes.attach(volume=volume,
                                          instance_uuid=instance_id,
                                          mountpoint=mount_point)
        return volume

    def _create_instances(self, num_machines):
        flavors_list = self.nova_client.flavors.list()
        images_list = self.nova_client.images.list()

        resources = [self.nova_client.servers.create(
            name='%s-%s' % ('vm', index),
            flavor=flavors_list[0],
            image=images_list[0]) for index in range(num_machines)]

        return resources

    def _delete_instances(self):
        instances = self.nova_client.servers.list()
        for instance in instances:
            try:
                self.nova_client.servers.delete(instance)
            except Exception:
                pass

    def _delete_volumes(self):
        volumes = self.cinder_client.volumes.list()
        for volume in volumes:
            try:
                self.cinder_client.volumes.detach(volume)
                self.cinder_client.volumes.force_delete(volume)
            except Exception:
                self.cinder_client.volumes.force_delete(volume)

    @staticmethod
    def _wait_for_status(max_waiting, func, **kwargs):
        count = 0
        while count < max_waiting:
            if func(**kwargs):
                return True
            count += 1
            time.sleep(2)
        LOG.info("wait_for_status - False ")
        return False

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
    def _create_graph_from_graph_dictionary(api_graph):
        graph = NXGraph()

        nodes = api_graph['nodes']
        for i in xrange(len(nodes)):
            graph.add_vertex(Vertex(str(i), nodes[i]))

        edges = api_graph['links']
        for i in xrange(len(edges)):
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
