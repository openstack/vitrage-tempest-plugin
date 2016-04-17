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

from vitrage import clients
from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources import AODH_DATASOURCE
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
        cls.conf.register_opts(list(OPTS), group='keystone_authtoken')
        cls.vitrage_client = \
            v_client.Client('1', session=keystone_client.get_session(cls.conf))
        cls.nova_client = clients.nova_client(cls.conf)
        cls.cinder_client = clients.cinder_client(cls.conf)

    def _create_volume_and_attach(self, name, size, instance_id, mount_point):
        volume = self.cinder_client.volumes.create(display_name=name,
                                                   size=size)
        time.sleep(3)
        self.cinder_client.volumes.attach(volume=volume,
                                          instance_uuid=instance_id,
                                          mountpoint=mount_point)

        self._wait_for_status(20,
                              self._check_num_volumes,
                              num_volumes=1)

        time.sleep(2)

        return volume

    def _create_instances(self, num_instances):
        flavors_list = self.nova_client.flavors.list()
        images_list = self.nova_client.images.list()

        resources = [self.nova_client.servers.create(
            name='%s-%s' % ('vm', index),
            flavor=flavors_list[0],
            image=images_list[0]) for index in range(num_instances)]

        self._wait_for_status(20,
                              self._check_num_instances,
                              num_instances=num_instances)
        time.sleep(2)

        return resources

    def _delete_instances(self):
        instances = self.nova_client.servers.list()
        for instance in instances:
            try:
                self.nova_client.servers.delete(instance)
            except Exception:
                pass

        self._wait_for_status(20,
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

    def _check_num_instances(self, num_instances=0):
        return len(self.nova_client.servers.list()) == num_instances

    def _check_num_volumes(self, num_volumes=0):
        return len(self.cinder_client.volumes.list()) == num_volumes

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
    def _wait_for_status(max_waiting, func, **kwargs):
        count = 0
        while count < max_waiting:
            if func(**kwargs):
                return True
            count += 1
            time.sleep(2)
        LOG.info("wait_for_status - False ")
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
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('instance_entities',
                                                        0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('instance_edges', 0)}
        validation_data.append(props)

        # cinder.volume
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: CINDER_VOLUME_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('volume_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('volume_edges', 0)}
        validation_data.append(props)

        # switch
        props = {VProps.CATEGORY: EntityCategory.RESOURCE,
                 VProps.TYPE: SWITCH,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('switch_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('switch_edges', 0)}
        validation_data.append(props)

        # aodh
        props = {VProps.CATEGORY: EntityCategory.ALARM,
                 VProps.TYPE: AODH_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('aodh_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('aodh_edges', 0)}
        validation_data.append(props)

        return validation_data

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
                VProps.CATEGORY: entity[VProps.CATEGORY],
                VProps.TYPE: entity[VProps.TYPE],
                VProps.IS_DELETED: False,
                VProps.IS_PLACEHOLDER: False
            }
            vertices = graph.get_vertices(vertex_attr_filter=query)
            self.assertEqual(entity[self.NUM_VERTICES_PER_TYPE],
                             len(vertices),
                             '%s%s' % ('Num vertices is incorrect for: %s',
                                       entity[VProps.TYPE]))

            num_edges = sum([len(graph.get_edges(vertex.vertex_id))
                             for vertex in vertices])
            self.assertEqual(entity[self.NUM_EDGES_PER_TYPE],
                             num_edges,
                             '%s%s' % ('Num edges is incorrect for: %s',
                                       entity[VProps.TYPE]))

    @staticmethod
    def get_flavor_id_from_list():
        text_out = utils.run_vitrage_command("nova flavor-list")
        try:
            flavor_id = utils.get_regex_result("\|\s+(\d+)\s+\|",
                                               text_out.splitlines()[3])
        except Exception as e:
            LOG.exception("Failed to get flavor id from the list %s ", e)
            return None

        LOG.debug("The flavor id from the list is " + flavor_id)
        return flavor_id

    @staticmethod
    def get_image_id_from_list():
        text_out = utils.run_vitrage_command("glance image-list")
        try:
            image_id = utils.get_regex_result("\|\s+(.*)\s+\|",
                                              text_out.splitlines()[3])
            image_id = image_id.split(" ")[0]
        except Exception as e:
            LOG.exception("Failed to get image id from the list %s ", e)
            return None

        LOG.debug("The image id from the list is " + image_id)
        return image_id

    @staticmethod
    def get_instance_id_by_name(vm_name):
        text_out = utils.run_vitrage_command("nova list")
        for line in text_out.splitlines():
            if vm_name in line:
                vm_id = utils.get_regex_result("\|\s+(.*)\s+\|", line)
                vm_id = vm_id.split(" ")[0]
                LOG.debug("The instance id from the nova list is " + vm_id)
                return vm_id
        return None

    @staticmethod
    def get_volume_id_by_name(vol_name):
        text_out = utils.run_vitrage_command("cinder list")
        for line in text_out.splitlines():
            if vol_name in line:
                vol_id = utils.get_regex_result("\|\s+(.*)\s+\|", line)
                vol_id = vol_id.split(" ")[0]
                LOG.debug("The volume id from the cinder list is " + vol_id)
                return vol_id
        return None

    @staticmethod
    def create_vm_with_exist_image(vm_name, flavor_id, image_id):
        utils.run_vitrage_command("nova boot " + vm_name + " --flavor " +
                                  flavor_id + " --image " + image_id)

        text_out = utils.run_vitrage_command("nova list")
        if vm_name in text_out:
            LOG.debug("The expected vm exist in the nova list")
        else:
            LOG.error("The expected vm not exist in the nova list")

    @staticmethod
    def create_volume_with_exist_size(vol_name):
        utils.run_vitrage_command("cinder create --name " + vol_name + " 5")

        text_out = utils.run_vitrage_command("cinder list")
        if vol_name in text_out:
            LOG.debug("The expected volume exist in the cinder list")
        else:
            LOG.error("The expected volume not exist in the cinder list")

    def attach_volume(self, vm_name, vol_name):
        vm_id = self.get_instance_id_by_name(vm_name)
        vol_id = self.get_volume_id_by_name(vol_name)

        utils.run_vitrage_command("nova volume-attach " + vm_id + " " + vol_id)

        text_out = utils.run_vitrage_command("cinder list")
        if vm_id in text_out:
            LOG.debug("The expected volume attached to vm")
        else:
            LOG.error("The expected volume did not attached to vm")
