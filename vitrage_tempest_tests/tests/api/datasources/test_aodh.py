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

from vitrage import clients
from vitrage_tempest_tests.tests.api.alarms.base import BaseAlarmsTest

LOG = logging.getLogger(__name__)


class TestAodhAlarm(BaseAlarmsTest):

    @classmethod
    def setUpClass(cls):
        super(TestAodhAlarm, cls).setUpClass()
        cls.ceilometer_client = clients.ceilometer_client(cls.conf)

    def test_alarm_with_resource_id(self):
        try:
            # create entities
            self._create_instances(num_instances=1)
            self._create_ceilometer_alarm(self._find_instance_resource_id())
            api_graph = self.vitrage_client.topology.get()
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=2,
                instance_entities=1, instance_edges=2,
                aodh_entities=1, aodh_edges=1)
            self._validate_graph_correctness(graph, 5, 4, entities)
        except Exception as e:
            LOG.exception(e)
        finally:
            self._delete_ceilometer_alarms()
            self._delete_instances()

    def test_alarm_without_resource_id(self):
        try:
            # create entities
            self._create_ceilometer_alarm()
            api_graph = self.vitrage_client.topology.get()
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=1,
                aodh_entities=1, aodh_edges=0)
            self._validate_graph_correctness(graph, 4, 2, entities)
        except Exception as e:
            LOG.exception(e)
        finally:
            self._delete_ceilometer_alarms()

    def _find_instance_resource_id(self):
        servers = self.nova_client.servers.list()
        return servers[0].id
