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
from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrage_tempest_plugin.tests.common.general_utils \
    import tempest_resources_dir
from vitrage_tempest_plugin.tests import utils

LOG = logging.getLogger(__name__)


class TestStaticPhysical(BaseVitrageTempest):
    NUM_SWITCH = 2

    def setUp(self):
        super(TestStaticPhysical, self).setUp()

    def tearDown(self):
        super(TestStaticPhysical, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestStaticPhysical, cls).setUpClass()

    @utils.tempest_logger
    def test_switches(self):
        try:
            # Action
            self._create_switches()

            # Calculate expected results
            api_graph = self.vitrage_client.topology.get(all_tenants=True)
            graph = self._create_graph_from_graph_dictionary(api_graph)
            entities = self._entities_validation_data(
                host_entities=1,
                host_edges=1 + self.NUM_SWITCH,
                switch_entities=self.NUM_SWITCH,
                switch_edges=self.NUM_SWITCH)
            num_entities = self.num_default_entities + self.NUM_SWITCH + \
                self.num_default_networks + self.num_default_ports
            num_edges = self.num_default_edges + self.NUM_SWITCH + \
                self.num_default_ports

            # Test Assertions
            self._validate_graph_correctness(graph,
                                             num_entities,
                                             num_edges,
                                             entities)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._delete_switches()

    @staticmethod
    def _create_switches():
        hostname = socket.gethostname()

        # template file
        resources_path = tempest_resources_dir() + '/static_physical/'
        file_path = resources_path + '/static_physical_configuration.yaml'
        with open(file_path, 'r') as f:
            template_data = f.read()
        template_data = template_data.replace('tmp-devstack', hostname)

        # new file
        new_file = open(
            '/etc/vitrage/static_datasources/'
            'static_physical_configuration.yaml', 'w')
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
