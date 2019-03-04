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

from datetime import datetime
from itertools import islice

import networkx as nx
from networkx.readwrite import json_graph
import six
from six.moves import zip

from oslo_log import log as logging
from oslo_utils import timeutils
from tempest.common import credentials_factory as common_creds
from tempest import test
from testtools.matchers import HasLength
from testtools.matchers import Not

from vitrage_tempest_plugin.tests.common.constants import AODH_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import \
    CINDER_VOLUME_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import EdgeProperties
from vitrage_tempest_plugin.tests.common.constants import EntityCategory
from vitrage_tempest_plugin.tests.common.constants import HEAT_STACK_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import \
    NEUTRON_NETWORK_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import \
    NEUTRON_PORT_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import NOVA_HOST_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import \
    NOVA_INSTANCE_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import NOVA_ZONE_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import OPENSTACK_CLUSTER
from vitrage_tempest_plugin.tests.common.constants import VertexProperties \
    as VProps
from vitrage_tempest_plugin.tests.common import general_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests import utils

import warnings

LOG = logging.getLogger(__name__)

IsEmpty = lambda: HasLength(0)
IsNotEmpty = lambda: Not(IsEmpty())

if six.PY2:
    class ResourceWarning(Warning):
        pass


class BaseVitrageTempest(test.BaseTestCase):
    """Base test class for All Vitrage tests."""

    credentials = ['primary']

    NUM_VERTICES_PER_TYPE = 'num_vertices'
    NUM_EDGES_PER_TYPE = 'num_edges_per_type'
    # TODO(e0ne): use credentials from the config
    DEMO_PROJECT_NAME = 'demo'

    def assert_list_equal(self, l1, l2, message=None):
        self.assertListEqual(l1, l2, message)

    def assert_dict_equal(self, d1, d2, message=None):
        self.assertDictEqual(d1, d2, message)

    def assert_set_equal(self, s1, s2, message=None):
        self.assertSetEqual(s1, s2, message)

    def assert_sequence_equal(self, s1, s2, message=None):
        self.assertSequenceEqual(s1, s2, message)

    def assert_tuple_equal(self, t1, t2, message=None):
        self.assertTupleEqual(t1, t2, message)

    def assert_items_equal(self, s1, s2, message=None):
        self.assertItemsEqual(s1, s2, message)

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
        logger = logging.getLogger('urllib3.connectionpool').logger
        logger.setLevel(logging.INFO)

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
        TempestClients.class_init(cls.os_primary.credentials)
        cls.vitrage_client = TempestClients.vitrage()
        cls.vitrage_client_for_demo_user = \
            TempestClients.vitrage_client_for_user()

        cls.num_default_networks = \
            len(TempestClients.neutron().list_networks()['networks'])
        cls.num_default_ports = cls._get_num_default_ports()
        cls.num_default_entities = 3
        cls.num_default_edges = 2
        cls.num_demo_tenant_networks = cls._calc_num_tenant_networks()

    @classmethod
    def _get_num_default_ports(cls):
        ports = TempestClients.neutron().list_ports()['ports']
        nova_ports = general_utils.all_matches(ports,
                                               device_owner='compute:nova')
        LOG.debug('ports: %s, nova_ports: %s', ports, nova_ports)
        return len(nova_ports)

    def _assert_graph_equal(self, g1, g2, msg=''):
        """Checks that two graphs are equals.

        This relies on assert_dict_equal when comparing the nodes and the
        edges of each graph.
        """
        g1_nodes = g1['nodes']
        g1_links = g1['links']

        g2_nodes = g2['nodes']
        g2_links = g1['links']

        to_remove = {'vitrage_sample_timestamp',
                     'update_timestamp',
                     'graph_index'}

        self._remove_keys_from_dicts(g1_nodes, g2_nodes, to_remove)

        self.assert_items_equal(g1_nodes, g2_nodes,
                                msg + "Nodes of each graph are not equal")
        self.assert_items_equal(g1_links, g2_links,
                                msg + "Edges of each graph are not equal")

    def _remove_keys_from_dicts(self, dictionaries1,
                                dictionaries2, keys_to_remove):
        self._delete_keys_from_dict(dictionaries1, keys_to_remove)
        self._delete_keys_from_dict(dictionaries2, keys_to_remove)

    @staticmethod
    def _delete_keys_from_dict(dictionaries, keys_to_remove):
        for dictionary in dictionaries:
            for key in keys_to_remove:
                if key in dictionary:
                    del dictionary[key]

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
                 VProps.VITRAGE_TYPE: 'switch',
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

    def _create_graph_from_tree_dictionary(self,
                                           api_graph,
                                           graph=None,
                                           ancestor=None):
        children = []
        graph = nx.MultiDiGraph() if not graph else graph

        if 'children' in api_graph:
            children = api_graph.copy()['children']
            del api_graph['children']

        vitrage_id = api_graph[VProps.VITRAGE_ID]
        graph.add_node(vitrage_id, **api_graph)
        if ancestor:
            graph.add_edge(ancestor[VProps.VITRAGE_ID], vitrage_id, 'label')

        for entity in children:
            self._create_graph_from_tree_dictionary(entity, graph, api_graph)

        return graph

    def _create_graph_from_graph_dictionary(self, api_graph):
        self.assertIsNotNone(api_graph)
        graph = nx.MultiDiGraph()

        nodes = api_graph['nodes']
        for i in range(len(nodes)):
            graph.add_node(str(i), **nodes[i])

        edges = api_graph['links']
        for i in range(len(edges)):
            graph.add_edge(str(edges[i]['source']),
                           str(edges[i]['target']),
                           EdgeProperties.RELATIONSHIP_TYPE)

        return graph

    @staticmethod
    def _get_vertices(graph, _filter):

        def check_vertex(data):
            data = data[1]
            for key, content in _filter.items():
                if not data.get(key) == content:
                    return False
            return True

        return list(filter(check_vertex, graph.nodes(data=True)))

    def _validate_graph_correctness(self,
                                    graph,
                                    num_entities,
                                    num_edges,
                                    entities):
        self.assertIsNotNone(graph)
        self.assertIsNotNone(entities)

        for entity in entities:
            vitrage_type = entity[VProps.VITRAGE_TYPE]
            vitrage_category = entity[VProps.VITRAGE_CATEGORY]
            query = {
                VProps.VITRAGE_CATEGORY: vitrage_category,
                VProps.VITRAGE_TYPE: vitrage_type,
                VProps.VITRAGE_IS_DELETED: False,
                VProps.VITRAGE_IS_PLACEHOLDER: False
            }
            vertices = self._get_vertices(graph, _filter=query)

            failed_msg = 'Num vertices is incorrect for: %s\n %s' % \
                         (vitrage_type, json_graph.node_link_data(graph))
            expected_num_vertices = entity[self.NUM_VERTICES_PER_TYPE]
            self.assertEqual(expected_num_vertices, len(vertices), failed_msg)

            # TODO(iafek): bug - edges between entities of the same type are
            # counted twice
            entity_num_edges = sum([len(graph.out_edges(vertex[0])) +
                                    len(graph.in_edges(vertex[0]))
                                    for vertex in vertices])

            failed_msg = 'Num edges is incorrect for: %s\n %s' % \
                         (vitrage_type, json_graph.node_link_data(graph))
            expected_num_edges = entity[self.NUM_EDGES_PER_TYPE]
            self.assertEqual(expected_num_edges, entity_num_edges, failed_msg)

        # this will unzip the vertices and create a tuple of
        # vertices with data only
        nodes = graph.nodes(data=True)
        graph_vertices = next(islice(zip(*nodes), 1, 2)) if len(nodes) else []
        self.assertEqual(num_entities, len(graph_vertices),
                         json_graph.node_link_data(graph))
        self.assertEqual(num_edges, len(graph.edges()),
                         json_graph.node_link_data(graph))

        self._validate_timestamps(graph_vertices)

    def _validate_timestamps(self, graph_vertices):
        self._validate_timestamp(graph_vertices, VProps.UPDATE_TIMESTAMP)
        self._validate_timestamp(graph_vertices,
                                 VProps.VITRAGE_SAMPLE_TIMESTAMP)

    def _validate_timestamp(self, graph_vertices, timestamp_name):
        for vertex in graph_vertices:
            timestamp = vertex.get(timestamp_name)
            if timestamp:
                try:
                    datetime.strptime(timestamp, utils.TIMESTAMP_FORMAT)
                except ValueError:
                    self.fail('Unexpected timestamp format of \'%s\' in: %s\n'
                              'The format should be: %s' %
                              (timestamp_name, vertex, utils.TIMESTAMP_FORMAT))

    @staticmethod
    def _calc_num_admin_tenant_networks():
        neutron_client = TempestClients.neutron()
        admin_creds = common_creds.get_configured_admin_credentials()
        tenant_networks = neutron_client.list_networks(
            tenant_id=admin_creds.project_id)['networks']
        return len(tenant_networks)

    @classmethod
    def _calc_num_tenant_networks(cls):
        neutron_client = TempestClients.neutron_client_for_user()
        tenant_networks = neutron_client.list_networks(
            tenant_id=cls.os_primary.credentials.project_id)['networks']
        return len(tenant_networks)

    @classmethod
    def _get_demo_tenant_id(cls):
        projects = TempestClients.keystone().projects.list()
        for project in projects:
            if cls.DEMO_PROJECT_NAME == project.name:
                return project.id
        return None
