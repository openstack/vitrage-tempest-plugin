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
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.utils import wait_for_status


def create_volume_and_attach(name, size, instance_id, mount_point):
    volume = TempestClients.cinder().volumes.create(name=name,
                                                    size=size)
    time.sleep(2)
    TempestClients.cinder().volumes.attach(volume=volume,
                                           instance_uuid=instance_id,
                                           mountpoint=mount_point)
    wait_for_status(30, _check_num_volumes, num_volumes=1, state='in-use')
    time.sleep(2)
    return volume


def delete_all_volumes():
    cinder = TempestClients.cinder()
    volumes = cinder.volumes.list()
    for volume in volumes:
        try:
            cinder.volumes.detach(volume)
            cinder.volumes.force_delete(volume)
        except Exception:
            cinder.volumes.reset_state(volume, state='available',
                                       attach_status='detached')
            cinder.volumes.force_delete(volume)
    wait_for_status(30, _check_num_volumes, num_volumes=0)
    time.sleep(2)


def _check_num_volumes(num_volumes=0, state=''):
    if len(TempestClients.cinder().volumes.list()) != num_volumes:
        return False

    return all(vars(volume)['status'].upper() == state.upper() and
               len(vars(volume)['attachments']) == 1
               for volume in TempestClients.cinder().volumes.list())
