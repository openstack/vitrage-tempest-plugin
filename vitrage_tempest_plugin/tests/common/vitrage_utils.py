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
from oslo_log import log as logging

from vitrage.common.constants import TemplateStatus
from vitrage.common.constants import TemplateTypes
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.utils import wait_for_status

LOG = logging.getLogger(__name__)

DOWN = 'down'
UP = 'up'


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
    try:
        hosts = TempestClients.vitrage().resource.list(
            NOVA_HOST_DATASOURCE, all_tenants=True)
    except Exception as e:
        LOG.exception("get_first_host failed with %s", e)
        hosts = TempestClients.vitrage().resource.list(
            NOVA_HOST_DATASOURCE, all_tenants=True)
    return g_utils.first_match(hosts, **kwargs)


def get_first_instance(**kwargs):
    instances = TempestClients.vitrage().resource.list(
        NOVA_INSTANCE_DATASOURCE, all_tenants=True)
    return g_utils.first_match(instances, **kwargs)


def add_template(filename='',
                 folder='templates/api',
                 template_type=TemplateTypes.STANDARD):
    full_path = g_utils.tempest_resources_dir() + '/' + folder + '/' + filename
    t = TempestClients.vitrage().template.add(full_path, template_type)
    if t and t[0]:
        wait_for_status(
            10,
            get_first_template,
            uuid=t[0]['uuid'], status=TemplateStatus.ACTIVE)
        return t[0]
    return None


def get_first_template(**kwargs):
    templates = TempestClients.vitrage().template.list()
    return g_utils.first_match(templates, **kwargs)


def delete_template(uuid):
    TempestClients.vitrage().template.delete(uuid)
    wait_for_status(
        10,
        lambda _id: True if not get_first_template(uuid=_id) else False,
        _id=uuid)
