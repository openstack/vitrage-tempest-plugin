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

service_option = cfg.BoolOpt("vitrage",
                             default=True,
                             help="Whether or not vitrage is expected to be "
                                  "available")

rca_service_group = cfg.OptGroup(name="root_cause_analysis_service",
                                 title="Root Cause Analysis Service Options")

RcaServiceGroup = [
    # RCA Service tempest configuration
    cfg.StrOpt("region",
               default="",
               help="The application_catalog region name to use. If empty, "
                    "the value of identity.region is used instead. "
                    "If no such region is found in the service catalog, "
                    "the first found one is used."),

    cfg.StrOpt("identity_version",
               default="v2",
               help="Default identity version for "
                    "REST client authentication.")
]
