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
from vitrage_tempest_tests.tests.api.topology.base import BaseTopologyTest

LOG = logging.getLogger(__name__)


class TestNova(BaseTopologyTest):

    @classmethod
    def setUpClass(cls):
        super(TestNova, cls).setUpClass()

    def test_nova_entities(self):
        try:
            # create entities
            self._create_entities(num_instances=3, end_sleep=10)
            api_graph = self.vitrage_client.topology.get()
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=4,
                instance_entities=3, instance_edges=3)
            self._validate_graph_correctness(graph, 6, 5, entities)
        except Exception as e:
            LOG.exception(e)
        finally:
            self._rollback_to_default()
