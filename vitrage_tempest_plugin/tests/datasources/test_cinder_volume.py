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
from vitrage_tempest_plugin.tests.api.topology.base import BaseTopologyTest
from vitrage_tempest_plugin.tests import utils

LOG = logging.getLogger(__name__)


class TestCinderVolume(BaseTopologyTest):
    NUM_INSTANCE = 3
    NUM_VOLUME = 1

    def setUp(self):
        super(TestCinderVolume, self).setUp()

    def tearDown(self):
        super(TestCinderVolume, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestCinderVolume, cls).setUpClass()

    @utils.tempest_logger
    def test_volume(self):
        try:
            # Action
            self._create_entities(num_instances=self.NUM_INSTANCE,
                                  num_volumes=self.NUM_VOLUME)

            # Calculate expected results
            api_graph = self.vitrage_client.topology.get(all_tenants=True)
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1,
                host_edges=self.NUM_INSTANCE + 1,
                instance_entities=self.NUM_INSTANCE,
                instance_edges=2 * self.NUM_INSTANCE + self.NUM_VOLUME,
                volume_entities=self.NUM_VOLUME,
                volume_edges=self.NUM_VOLUME)
            num_entities = self.num_default_entities + self.NUM_VOLUME + \
                2 * self.NUM_INSTANCE + self.num_default_ports + \
                self.num_default_networks
            num_edges = self.num_default_edges + 3 * self.NUM_INSTANCE + \
                self.NUM_VOLUME + self.num_default_ports

            # Test Assertions
            self._validate_graph_correctness(graph,
                                             num_entities,
                                             num_edges,
                                             entities)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._rollback_to_default()
