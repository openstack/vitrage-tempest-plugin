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


from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrage_tempest_plugin.tests.base import IsNotEmpty
from vitrage_tempest_plugin.tests.base import LOG
from vitrage_tempest_plugin.tests.common import cinder_utils
from vitrage_tempest_plugin.tests.common import nova_utils


class BaseTopologyTest(BaseVitrageTempest):
    """Topology test class for Vitrage API tests."""

    def tearDown(self):
        super(BaseTopologyTest, self).tearDown()
        self._rollback_to_default()

    def _rollback_to_default(self):
        self._delete_entities()
        api_graph = self.vitrage_client.topology.get(
            root=None,
            all_tenants=True)
        graph = self._create_graph_from_graph_dictionary(api_graph)
        entities = self._entities_validation_data()
        num_default_entities = self.num_default_entities + \
            self.num_default_networks + self.num_default_ports
        num_default_edges = self.num_default_edges + self.num_default_ports
        try:
            self._validate_graph_correctness(graph,
                                             num_default_entities,
                                             num_default_edges,
                                             entities)
        except AssertionError as e:
            LOG.error(e)

    def _create_entities(self, num_instances, num_volumes=0, end_sleep=3):
        resources = nova_utils.create_instances(num_instances)

        self.assertThat(resources, IsNotEmpty(),
                        'The instances list is empty')
        if num_volumes > 0:
            cinder_utils.create_volume_and_attach('volume-1', 1,
                                                  resources[0].id,
                                                  '/tmp/vda')

        # waiting until all the entities creation were processed by the
        # entity graph processor
        time.sleep(end_sleep)

    @staticmethod
    def _delete_entities():
        cinder_utils.delete_all_volumes()
        nova_utils.delete_all_instances()

        # waiting until all the entities deletion were processed by the
        # entity graph processor
        time.sleep(2)

    @staticmethod
    def _graph_query():
        return '{"and": [{"==": {"vitrage_category": "RESOURCE"}},' \
               '{"==": {"vitrage_is_deleted": false}},' \
               '{"==": {"vitrage_is_placeholder": false}},' \
               '{"or": [{"==": {"vitrage_type": "openstack.cluster"}},' \
               '{"==": {"vitrage_type": "nova.instance"}},' \
               '{"==": {"vitrage_type": "nova.host"}},' \
               '{"==": {"vitrage_type": "nova.zone"}}]}]}'

    @staticmethod
    def _tree_query():
        return '{"and": [{"==": {"vitrage_category": "RESOURCE"}},' \
               '{"==": {"vitrage_is_deleted": false}},' \
               '{"==": {"vitrage_is_placeholder": false}},' \
               '{"or": [{"==": {"vitrage_type": "openstack.cluster"}},' \
               '{"==": {"vitrage_type": "nova.host"}},' \
               '{"==": {"vitrage_type": "nova.zone"}}]}]}'

    @staticmethod
    def _graph_no_match_query():
        return '{"and": [{"==": {"vitrage_category": "test"}},' \
               '{"==": {"vitrage_is_deleted": false}},' \
               '{"==": {"vitrage_is_placeholder": false}},' \
               '{"or": [{"==": {"vitrage_type": "openstack.cluster"}},' \
               '{"==": {"vitrage_type": "nova.instance"}},' \
               '{"==": {"vitrage_type": "nova.host"}},' \
               '{"==": {"vitrage_type": "nova.zone"}}]}]}'

    @staticmethod
    def _tree_no_match_query():
        return '{"and": [{"==": {"vitrage_category": "test"}},' \
               '{"==": {"vitrage_is_deleted": false}},' \
               '{"==": {"vitrage_is_placeholder": false}},' \
               '{"or": [{"==": {"vitrage_type": "openstack.cluster"}},' \
               '{"==": {"vitrage_type": "nova.host"}},' \
               '{"==": {"vitrage_type": "nova.zone"}}]}]}'
