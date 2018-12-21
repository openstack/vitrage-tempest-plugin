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
]
