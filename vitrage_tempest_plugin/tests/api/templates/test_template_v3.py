# Copyright 2019 - Nokia
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

from oslo_log import log as logging

from vitrage_tempest_plugin.tests.api.templates.test_template_v2 \
    import TestTemplatesApis

LOG = logging.getLogger(__name__)

WITH_PARAMS_TEMPLATE = 'v3_with_params.yaml'
WITH_DEFAULT_PARAMS_TEMPLATE = 'v3_with_default_params.yaml'

TEMPLATE_STRING = """
metadata:
 version: 3
 name: template1
 description: simple template
 type: standard
entities:
 alarm:
  name: cpu problem
 host:
  type: nova.host
scenarios:
 - condition: alarm [ on ] host
   actions:
     - set_state:
        state: ERROR
        target: host
"""


class TestTemplatesV3(TestTemplatesApis):

    def test_template_validate_with_missing_parameters(self):
        self._validate_with_missing_parameters(WITH_PARAMS_TEMPLATE)

    def test_template_validate_with_missing_parameter(self):
        self._validate_with_missing_parameter(WITH_PARAMS_TEMPLATE)

    def test_template_validate_with_parameters(self):
        self._validate_with_parameters(WITH_PARAMS_TEMPLATE)

    def test_template_validate_with_default_parameters(self):
        self._validate_with_default_parameters(WITH_DEFAULT_PARAMS_TEMPLATE)

    def test_template_add_with_missing_parameters(self):
        self._add_with_missing_parameters(WITH_PARAMS_TEMPLATE)

    def test_template_add_with_missing_parameter(self):
        self._add_with_missing_parameter(WITH_PARAMS_TEMPLATE)

    def test_template_add_with_parameters(self):
        self._add_with_parameters(WITH_PARAMS_TEMPLATE)

    def test_template_add_with_default_parameters(self):
        self._add_with_default_parameters(WITH_DEFAULT_PARAMS_TEMPLATE)

    def test_template_add_by_string(self):
        self._add_by_string(TEMPLATE_STRING)
