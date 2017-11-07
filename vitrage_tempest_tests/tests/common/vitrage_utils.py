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
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources import NOVA_HOST_DATASOURCE
from vitrage_tempest_tests.tests.common.tempest_clients import TempestClients


def get_first_host():
    nodes = TempestClients.vitrage().topology.get(all_tenants=True)['nodes']
    return next(
        (n for n in nodes if n[VProps.VITRAGE_TYPE] == NOVA_HOST_DATASOURCE),
        None)
