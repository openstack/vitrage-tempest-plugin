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

import six
import sys
import traceback

from oslo_log import log as logging
from oslo_utils import timeutils
from oslotest import base
from testtools.matchers import HasLength

from vitrage.common.constants import EdgeProperties
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
from vitrage import service
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests import utils

import warnings

LOG = logging.getLogger(__name__)

IsEmpty = lambda: HasLength(0)

if six.PY2:
    class ResourceWarning(Warning):
        pass


class BaseVitrageTempest(base.BaseTestCase):
    """Base test class for All Vitrage tests."""

    NUM_VERTICES_PER_TYPE = 'num_vertices'
    NUM_EDGES_PER_TYPE = 'num_edges_per_type'

    def assert_list_equal(self, l1, l2):
        if tuple(sys.version_info)[0:2] < (2, 7):
            # for python 2.6 compatibility
            self.assertEqual(l1, l2)
        else:
            super(BaseVitrageTempest, self).assertListEqual(l1, l2)

    def assert_dict_equal(self, d1, d2, message):
        if tuple(sys.version_info)[0:2] < (2, 7):
            # for python 2.6 compatibility
            self.assertEqual(d1, d2)
        else:
            super(BaseVitrageTempest, self).assertDictEqual(d1, d2, message)

    def assert_timestamp_equal(self, first, second, msg=None):
        """Checks that two timestamps are equals.

        This relies on assertAlmostEqual to avoid rounding problem, and only
        checks up the first microsecond values.

        """
        return self.assertAlmostEqual(timeutils.delta_seconds(first, second),
                                      0.0,
                                      places=5, msg=msg)

    def assert_is_empty(self, obj):
        try:
            if len(obj) != 0:
                self.fail("%s is not empty" % type(obj))
        except (TypeError, AttributeError):
            self.fail("%s doesn't have length" % type(obj))

    def assert_is_not_empty(self, obj):
        try:
            if len(obj) == 0:
                self.fail("%s is empty" % type(obj))
        except (TypeError, AttributeError):
            self.fail("%s doesn't have length" % type(obj))

    def setUp(self):
        super(BaseVitrageTempest, self).setUp()
        warnings.filterwarnings(action="ignore",
                                message="unclosed",
                                category=ResourceWarning)

    def tearDown(self):
        super(BaseVitrageTempest, self).tearDown()
        warnings.filterwarnings(action="ignore",
                                message="unclosed",
                                category=ResourceWarning)

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        super(BaseVitrageTempest, cls).setUpClass()
        warnings.filterwarnings(action="ignore",
                                message="unclosed",
                                category=ResourceWarning)
        cls.conf = service.prepare_service([])
        TempestClients.class_init(cls.conf)
        cls.vitrage_client = TempestClients.vitrage()

        cls.num_default_networks = \
            len(TempestClients.neutron().list_networks()['networks'])
        cls.num_default_ports = 0
        cls.num_default_entities = 3
        cls.num_default_edges = 2

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
                                edges[i][EdgeProperties.RELATIONSHIP_TYPE]))

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

    def _entities_validation_data(self, **kwargs):
        validation_data = []

        # openstack.cluster
        props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                 VProps.VITRAGE_TYPE: OPENSTACK_CLUSTER,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('cluster_entities', 1),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('cluster_edges', 1)}
        validation_data.append(props)

        # nova.zone
        props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                 VProps.VITRAGE_TYPE: NOVA_ZONE_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('zone_entities', 1),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('zone_edges', 2)}
        validation_data.append(props)

        # nova.host
        props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                 VProps.VITRAGE_TYPE: NOVA_HOST_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get('host_entities', 1),
                 self.NUM_EDGES_PER_TYPE: kwargs.get('host_edges', 1)}
        validation_data.append(props)

        # nova.instance
        props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                 VProps.VITRAGE_TYPE: NOVA_INSTANCE_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'instance_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'instance_edges', 0)}
        validation_data.append(props)

        # cinder.volume
        props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                 VProps.VITRAGE_TYPE: CINDER_VOLUME_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'volume_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'volume_edges', 0)}
        validation_data.append(props)

        # switch
        props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                 VProps.VITRAGE_TYPE: SWITCH,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'switch_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'switch_edges', 0)}
        validation_data.append(props)

        # aodh
        props = {VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
                 VProps.VITRAGE_TYPE: AODH_DATASOURCE,
                 self.NUM_VERTICES_PER_TYPE: kwargs.get(
                     'aodh_entities', 0),
                 self.NUM_EDGES_PER_TYPE: kwargs.get(
                     'aodh_edges', 0)}
        validation_data.append(props)

        # neutron.network
        if kwargs.get('network_entities') is not None:
            props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                     VProps.VITRAGE_TYPE: NEUTRON_NETWORK_DATASOURCE,
                     self.NUM_VERTICES_PER_TYPE: kwargs.get(
                         'network_entities', 0),
                     self.NUM_EDGES_PER_TYPE: kwargs.get(
                         'network_edges', 0)}
            validation_data.append(props)

        # neutron.port
        if kwargs.get('port_entities') is not None:
            props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                     VProps.VITRAGE_TYPE: NEUTRON_PORT_DATASOURCE,
                     self.NUM_VERTICES_PER_TYPE: kwargs.get(
                         'port_entities', 0),
                     self.NUM_EDGES_PER_TYPE: kwargs.get(
                         'port_edges', 0)}
            validation_data.append(props)

        # heat.stack
        props = {VProps.VITRAGE_CATEGORY: EntityCategory.RESOURCE,
                 VProps.VITRAGE_TYPE: HEAT_STACK_DATASOURCE,
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
                VProps.VITRAGE_CATEGORY: entity[VProps.VITRAGE_CATEGORY],
                VProps.VITRAGE_TYPE: entity[VProps.VITRAGE_TYPE],
                VProps.VITRAGE_IS_DELETED: False,
                VProps.VITRAGE_IS_PLACEHOLDER: False
            }
            vertices = graph.get_vertices(vertex_attr_filter=query)
            self.assertEqual(entity[self.NUM_VERTICES_PER_TYPE],
                             len(vertices),
                             '%s%s' % ('Num vertices is incorrect for: ',
                                       entity[VProps.VITRAGE_TYPE]))

            entity_num_edges = sum([len(graph.get_edges(vertex.vertex_id))
                                    for vertex in vertices])
            self.assertEqual(entity[self.NUM_EDGES_PER_TYPE],
                             entity_num_edges,
                             '%s%s' % ('Num edges is incorrect for: ',
                                       entity[VProps.VITRAGE_TYPE]))

        self.assertEqual(num_entities, graph.num_vertices())
        self.assertEqual(num_edges, graph.num_edges())

    @staticmethod
    def _get_value(item, key):
        return utils.uni2str(item[key])

    def _print_entity_graph(self):
        api_graph = TempestClients.vitrage().topology.get(all_tenants=True)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        LOG.info('Entity Graph: \n%s', graph.json_output_graph())

    def _handle_exception(self, exception):
        traceback.print_exc()
        LOG.exception(exception)
        self._print_entity_graph()
