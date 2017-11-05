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
from vitrage_tempest_tests.tests.common.tempest_clients import TempestClients
from vitrage_tempest_tests.tests.utils import uni2str


def get_public_network():
    nets = TempestClients.neutron().list_networks()
    return next(
        (n for n in nets['networks'] if uni2str(n[VProps.NAME]) == 'public'),
        None)
