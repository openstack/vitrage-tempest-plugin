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

from oslo_log import log as logging

from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common import glance_utils
from vitrage_tempest_plugin.tests.common import neutron_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.utils import wait_for_status

LOG = logging.getLogger(__name__)


def create_instances(num_instances=1, set_public_network=True, name='vm'):
    nics = []
    flavor = get_first_flavor()
    image = glance_utils.get_first_image()
    if set_public_network:
        public_net = neutron_utils.get_public_network()
        if public_net:
            nics = [{'net-id': public_net['id']}]

    for i in range(3):
        success, resources = _create_instances(flavor, image, name, nics,
                                               num_instances)
        time.sleep(2)
        if success:
            return resources
        if not success:
            LOG.warning("create instance failed, delete and retry %s",
                        resources)
            delete_created_instances(resources)
            time.sleep(10)
    raise AssertionError("Unable to create vms, retries failed")


def _create_instances(flavor, image, name, nics, num_instances):
    LOG.info("create instance with flavor=%s image=%s" % (flavor, image))
    resources = [TempestClients.nova().servers.create(
        name='%s-%s' % (name, index),
        flavor=flavor,
        image=image,
        nics=nics) for index in range(num_instances)]
    success = wait_for_status(
        30, check_new_instances, ids=[instance.id for instance in resources])
    return success, resources


def delete_created_instances(instances):
    if not instances:
        return
    for instance in instances:
        delete_all_instances(id=instance.id)


def delete_all_instances(**kwargs):
    instances = TempestClients.nova().servers.list()
    instances_to_delete = g_utils.all_matches(instances, **kwargs)
    for item in instances_to_delete:
        try:
            TempestClients.nova().servers.force_delete(item)
        except Exception:
            LOG.exception('Failed to force delete instance %s', item.id)
    wait_for_status(
        30,
        check_deleted_instances,
        ids=[instance.id for instance in instances_to_delete])
    time.sleep(2)


def get_first_flavor():
    return TempestClients.nova().flavors.list(sort_key='memory_mb')[0]


def check_deleted_instances(ids):
    servers = TempestClients.nova().servers.list()
    for s in servers:
        if s.id in ids:
            return False
    return True


def check_new_instances(ids):
    servers = TempestClients.nova().servers.list()
    for _id in ids:
        ok = False
        for s in servers:
            if _id == s.id and s.status.lower() == 'active':
                ok = True
                break
        if not ok:
            return False
    return True
