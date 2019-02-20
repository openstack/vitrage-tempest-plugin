# Copyright 2015
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_config import cfg

service_available_group = cfg.OptGroup(name="service_available",
                                       title="Available OpenStack Services")

ServiceAvailableGroup = [cfg.BoolOpt("vitrage",
                                     default=True,
                                     help="Whether or not vitrage is expected "
                                     "to be available")]

rca_service_group = cfg.OptGroup(name="root_cause_analysis_service",
                                 title="Root Cause Analysis Service Options")

RcaServiceGroup = [
    # RCA Service tempest configuration
    cfg.IntOpt('instances_per_host',
               default=2,
               help="Number of instances per host in mock graph datasource"),
    cfg.IntOpt('snapshots_interval',
               default=120,
               min=10,
               help='Time to wait between subsequent datasource snapshots'),
    cfg.IntOpt('zabbix_alarms_per_host', default=2),
    cfg.StrOpt('aodh_version', default='2', help='Aodh version'),
    cfg.StrOpt('ceilometer_version', default='2', help='Ceilometer version'),
    cfg.StrOpt('nova_version', default='2.11', help='Nova version'),
    cfg.StrOpt('cinder_version', default='3', help='Cinder version'),
    cfg.StrOpt('glance_version', default='2', help='Glance version'),
    cfg.StrOpt('heat_version', default='1', help='Heat version'),
    cfg.StrOpt('mistral_version', default='2', help='Mistral version'),
    cfg.StrOpt('gnocchi_version', default='1', help='Gnocchi version'),
    cfg.StrOpt('trove_version', default='1', help='Trove version'),
]
