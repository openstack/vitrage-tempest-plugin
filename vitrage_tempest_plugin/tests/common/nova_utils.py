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
import time

from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common import glance_utils
from vitrage_tempest_plugin.tests.common import neutron_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.utils import wait_for_status


def create_instances(num_instances=1, set_public_network=False, name='vm'):
    nics = []
    flavor = get_first_flavor()
    image = glance_utils.get_first_image()
    if set_public_network:
        public_net = neutron_utils.get_public_network()
        if public_net:
            nics = [{'net-id': public_net['id']}]

    resources = [TempestClients.nova().servers.create(
        name='%s-%s' % (name, index),
        flavor=flavor,
        image=image,
        nics=nics) for index in range(num_instances)]
    wait_for_status(30, _check_num_instances, num_instances=num_instances,
                    state='active')
    time.sleep(2)
    return resources


def delete_all_instances(**kwargs):
    instances = TempestClients.nova().servers.list()
    instances_to_delete = g_utils.all_matches(instances, **kwargs)
    for item in instances_to_delete:
        try:
            TempestClients.nova().servers.force_delete(item)
        except Exception:
            pass
    wait_for_status(
        30,
        _check_num_instances,
        num_instances=len(instances) - len(instances_to_delete))
    time.sleep(2)


def get_first_flavor():
    return TempestClients.nova().flavors.list()[0]


def _check_num_instances(num_instances=0, state=''):
    if len(TempestClients.nova().servers.list()) != num_instances:
        return False

    return all(instance.__dict__['status'].upper() == state.upper()
               for instance in TempestClients.nova().servers.list())
