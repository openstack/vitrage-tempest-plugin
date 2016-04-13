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

import random
import time

from oslo_log import log as logging

from vitrage import clients
from vitrage_tempest_tests.tests.api.base import BaseApiTest

LOG = logging.getLogger(__name__)


class TestAodhAlarm(BaseApiTest):

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
        finally:
            self._delete_ceilometer_alarms()

    def _create_ceilometer_alarm(self, resource_id=None):
        aodh_request = self._aodh_request(resource_id=resource_id)
        self.ceilometer_client.alarms.create(**aodh_request)
        self._wait_for_status(20,
                              self._check_num_alarms,
                              num_alarms=1)
        time.sleep(25)

    def _delete_ceilometer_alarms(self):
        alarms = self.ceilometer_client.alarms.list()
        for alarm in alarms:
            self.ceilometer_client.alarms.delete(alarm.alarm_id)
        self._wait_for_status(20,
                              self._check_num_alarms,
                              num_alarms=0)
        time.sleep(25)

    def _check_num_alarms(self, num_alarms=0):
        return len(self.ceilometer_client.alarms.list()) == num_alarms

    def _aodh_request(self, resource_id=None):
        query = []
        if resource_id:
            query = [
                dict(
                    field=u'resource_id',
                    type='',
                    op=u'eq',
                    value=resource_id)
            ]

        random_name = '%s-%s' % ('test', random.randrange(0, 100000, 1))
        return dict(
            name=random_name,
            description=u'test alarm',
            event_rule=dict(query=query),
            severity='low',
            state='alarm',  # ok/alarm/insufficient data
            type=u'event')

    def _find_instance_resource_id(self):
        servers = self.nova_client.servers.list()
        return servers[0].id
