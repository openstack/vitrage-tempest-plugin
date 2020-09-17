#  Copyright 2019 - Nokia Corporation
#
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import socket

from testtools import matchers

from vitrage_tempest_plugin.tests.base import BaseVitrageTempest


SERVICES = {
    'ApiWorker',
    'EvaluatorWorker',
    'MachineLearningService',
    'PersistorService',
    'SnmpParsingService',
    'vitrageuWSGI',
    'VitrageNotifierService'
}


class ServiceTest(BaseVitrageTempest):
    def test_service_list(self):
        services = self.vitrage_client.service.list()

        self.check_all_equal(services, SERVICES)
        self.check_all_hosted(services, socket.gethostname())
        self.check_different_process_ids_for(services)

    def check_all_equal(self, services, expected_svc_names):
        names = {service['name'].split(' ')[0] for service in services}
        self.assert_set_equal(expected_svc_names, names)

    def check_all_hosted(self, services, hostname):
        hostnames = {service['hostname'] for service in services}
        self.assert_set_equal({hostname}, hostnames)

    def check_different_process_ids_for(self, services):
        num_services = len(services)
        process_ids = {service['process'] for service in services}
        self.assertThat(process_ids, matchers.HasLength(num_services))
