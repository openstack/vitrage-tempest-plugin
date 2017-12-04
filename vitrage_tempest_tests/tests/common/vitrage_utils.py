# Copyright 2017 - Nokia
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
from datetime import datetime

from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage_tempest_tests.tests.api.event.base import DOWN
from vitrage_tempest_tests.tests.api.event.base import UP
from vitrage_tempest_tests.tests.common import general_utils as g_utils
from vitrage_tempest_tests.tests.common.tempest_clients import TempestClients


def generate_fake_host_alarm(hostname, event_type, enabled=True):
    details = {
        'hostname': hostname,
        'source': 'fake_tempest_monitor',
        'cause': 'another alarm',
        'severity': 'critical',
        'status': DOWN if enabled else UP,
        'monitor_id': 'fake tempest monitor id',
        'monitor_event_id': '111',
    }
    event_time = datetime.now()
    event_time_iso = event_time.isoformat()
    TempestClients.vitrage().event.post(event_time_iso, event_type, details)


def get_first_host(**kwargs):
    hosts = TempestClients.vitrage().resource.list(
        NOVA_HOST_DATASOURCE, all_tenants=True)
    return g_utils.first_match(hosts, **kwargs)


def get_first_instance(**kwargs):
    instances = TempestClients.vitrage().resource.list(
        NOVA_INSTANCE_DATASOURCE, all_tenants=True)
    return g_utils.first_match(instances, **kwargs)
