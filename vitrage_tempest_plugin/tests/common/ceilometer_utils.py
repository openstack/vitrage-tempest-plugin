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
import random
import time
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients


def create_ceilometer_alarm(resource_id=None, name=None, unic=True):
    if not name:
        name = '%s-%s' % ('test_', random.randrange(0, 100000, 1))
    elif unic:
        name = '%s-%s' % (name, random.randrange(0, 100000, 1))

    aodh_request = _aodh_request(resource_id=resource_id, name=name)
    TempestClients.ceilometer().alarms.create(**aodh_request)
    time.sleep(45)


def delete_all_ceilometer_alarms():
    alarms = TempestClients.ceilometer().alarms.list()
    for alarm in alarms:
        TempestClients.ceilometer().alarms.delete(alarm.alarm_id)
    time.sleep(120)


def _aodh_request(resource_id=None, name=None):
    query = []
    if resource_id:
        query = [
            dict(
                field=u'traits.resource_id',
                type='',
                op=u'eq',
                value=resource_id)
        ]

    return dict(
        name=name,
        description=u'test alarm',
        event_rule=dict(query=query),
        severity='low',
        state='alarm',
        type=u'event')
