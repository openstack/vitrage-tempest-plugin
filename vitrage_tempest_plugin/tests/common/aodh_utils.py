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

from oslo_serialization import jsonutils

from vitrage_tempest_plugin.tests.common.constants import AodhProperties as \
    AodhProps
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients


def create_aodh_alarm(resource_id=None, name=None, unic=True):
    if not name:
        name = '%s-%s' % ('test_', random.randrange(0, 100000, 1))
    elif unic:
        name = '%s-%s' % (name, random.randrange(0, 100000, 1))

    aodh_request = _aodh_request('event',
                                 resource_id=resource_id,
                                 name=name)
    TempestClients.aodh().alarm.create(aodh_request)
    time.sleep(20)


def create_aodh_metrics_threshold_alarm(resource_id=None, name=None):
    if not name:
        name = '%s-%s' % ('test_', random.randrange(0, 100000, 1))
    met = TempestClients.gnocchi().metric.create(resource_id=resource_id,
                                                 name='test',
                                                 archive_policy_name='high')
    metric = met[AodhProps.ID]
    rule_opts = dict(
        threshold='100',
        aggregation_method='mean',
        comparison_operator='lt',
        metrics=[metric]
    )
    rule = {
        AodhProps.METRICS_THRESHOLD_RULE: rule_opts
    }
    aodh_request = _aodh_request(AodhProps.METRICS_THRESHOLD,
                                 resource_id=resource_id,
                                 name=name,
                                 rule=rule)
    TempestClients.aodh().alarm.create(aodh_request)
    time.sleep(10)


def create_aodh_resources_threshold_alarm(resource_id, name=None):
    if not name:
        name = '%s-%s' % ('test_', random.randrange(0, 100000, 1))

    gnocchi_resource = _get_gnocchi_resource_id()
    met = TempestClients.gnocchi().metric.create(resource_id=gnocchi_resource,
                                                 name='test',
                                                 archive_policy_name='high')
    metric = met[AodhProps.ID]
    rule_opts = dict(
        threshold='100',
        aggregation_method='mean',
        comparison_operator='lt',
        metric=metric,
        resource_type='nova.instance'
    )
    rule = {
        AodhProps.RESOURCES_THRESHOLD_RULE: rule_opts
    }
    aodh_request = _aodh_request(AodhProps.RESOURCES_THRESHOLD,
                                 resource_id=resource_id,
                                 name=name,
                                 rule=rule)
    TempestClients.aodh().alarm.create(aodh_request)
    time.sleep(10)


def delete_all_aodh_alarms():
    alarms = TempestClients.aodh().alarm.list()
    for alarm in alarms:
        TempestClients.aodh().alarm.delete(alarm[AodhProps.ALARM_ID])
    time.sleep(10)


def delete_all_gnocchi_metrics():
    metrics = TempestClients.gnocchi().metric.list()
    for metric in metrics:
        TempestClients.gnocchi().metric.delete(metric[AodhProps.ID])
    time.sleep(10)


def _get_gnocchi_resource_id():
    return TempestClients.gnocchi().resource.list()[0][AodhProps.ID]


def _aodh_request(type, resource_id=None, name=None, rule=None):
    query = []
    if resource_id:
        query = [
            dict(
                field='traits.resource_id',
                type='',
                op='eq',
                value=resource_id)
        ]
    request = dict(
        name=name,
        description='test alarm',
        severity='low',
        state='alarm',
        type=type)

    if not rule:
        rule = dict(event_rule=(dict(query=query)))
    elif rule.get(AodhProps.RESOURCES_THRESHOLD_RULE):
        # aggregation_by_resources_threshold requests are different from other
        # alarms, update accordingly
        query[0].update(dict(field='resource_id'))
        rule[AodhProps.RESOURCES_THRESHOLD_RULE].update(dict(
            query=jsonutils.dump_as_bytes(query)))

    request.update(rule)
    return request
