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

import os
import socket
import time

from oslo_log import log as logging
from vitrage_tempest_tests.tests.api.base import BaseApiTest


LOG = logging.getLogger(__name__)


class TestStaticPhysical(BaseApiTest):

    @classmethod
    def setUpClass(cls):
        super(TestStaticPhysical, cls).setUpClass()

    def test_switches(self):
        try:
            # create entities
            self._create_switches()
            api_graph = self.vitrage_client.topology.get()
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1, host_edges=3,
                switch_entities=2, switch_edges=2)
            self._validate_graph_correctness(graph, 5, 4, entities)
        except Exception as e:
            LOG.exception(e)
        finally:
            self._delete_switches()

    @staticmethod
    def _create_switches():
        hostname = socket.gethostname()

        # template file
        file_path = '/opt/stack/vitrage/vitrage_tempest_tests/tests/' \
                    'resources/static_physical/' \
                    'static_physical_configuration.yaml'
        with open(file_path, 'rb') as f:
            template_data = f.read()
        template_data = template_data.replace('tmp-devstack', hostname)

        # new file
        new_file = open(
            '/etc/vitrage/static_datasources/'
            'static_physical_configuration.yaml', 'wb')
        new_file.write(template_data)
        new_file.close()

        time.sleep(25)

    @staticmethod
    def _delete_switches():
        path = '/etc/vitrage/static_datasources/' \
               'static_physical_configuration.yaml'
        if os.path.exists(path):
            os.remove(path)

        time.sleep(25)
