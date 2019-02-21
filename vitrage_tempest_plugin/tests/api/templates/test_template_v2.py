# Copyright 2018 - Nokia
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

from vitrage_tempest_plugin.tests.api.templates.base import BaseTemplateTest

LOG = logging.getLogger(__name__)

EXECUTE_MISTRAL_TEMPLATE = 'v2_execute_mistral.yaml'
EQUIVALENCE_TEMPLATE = 'v2_equivalence_templates.yaml'
DEFINITION_TEMPLATE = 'v2_definition_template.yaml'
NO_TYPE_TEMPLATE = 'v2_no_type_template.yaml'
WITH_PARAMS_TEMPLATE = 'v2_with_params.yaml'

FAILED_TO_RESOLVE_PARAM = 'Failed to resolve parameter'
ERROR_STATUS = 'ERROR'
LOADING_STATUS = 'LOADING'
TEMPLATE_VALIDATION_OK = 'Template validation is OK'


class TestTemplatesApis(BaseTemplateTest):

    def tearDown(self):
        super(TestTemplatesApis, self).tearDown()
        self._delete_templates()

    def _validate_no_type_templates(self, template_name):
        path = self.TEST_PATH + template_name
        validation = self.vitrage_client.template.validate(path=path)
        self._assert_validate_result(
            validation, path, negative=True, status_code='')

    def _validate_standard_template(self, template_name):
        path = self.TEST_PATH + template_name
        validation = self.vitrage_client.template.validate(path=path)
        self._assert_validate_result(validation, path)

    def _validate_definition_template(self, template_name):
        path = self.TEST_PATH + template_name
        validation = self.vitrage_client.template.validate(path=path)
        self._assert_validate_result(validation, path)

    def _validate_with_missing_parameters(self, template_name):
        path = self.TEST_PATH + template_name
        validation = self.vitrage_client.template.validate(path=path)
        self._assert_validate_result(
            validation, path, negative=True, status_code=163)

    def _validate_with_missing_parameter(self, template_name):
        path = self.TEST_PATH + template_name
        params = {'template_name': 'My template 1',
                  'new_state': 'SUBOPTIMAL'}
        validation = \
            self.vitrage_client.template.validate(path=path, params=params)
        self._assert_validate_result(
            validation, path, negative=True, status_code=163)

    def _validate_with_parameters(self, template_name):
        path = self.TEST_PATH + template_name
        params = {'template_name': 'My template 1',
                  'alarm_type': 'Monitor1',
                  'alarm_name': 'My alarm',
                  'new_state': 'SUBOPTIMAL'}
        validation = \
            self.vitrage_client.template.validate(path=path, params=params)
        self._assert_validate_result(validation, path)

    def _add_with_missing_parameters(self, template_name):
        path = self.TEST_PATH + template_name
        result = self.vitrage_client.template.add(path=path)
        self._assert_add_result(result, ERROR_STATUS, FAILED_TO_RESOLVE_PARAM)

    def _add_with_missing_parameter(self, template_name):
        path = self.TEST_PATH + template_name
        params = {'template_name': 'My template 1',
                  'new_state': 'SUBOPTIMAL'}
        result = self.vitrage_client.template.add(path=path, params=params)
        self._assert_add_result(result, ERROR_STATUS, FAILED_TO_RESOLVE_PARAM)

    def _add_with_parameters(self, template_name):
        path = self.TEST_PATH + template_name
        params = {'template_name': 'My template 1',
                  'alarm_type': 'Monitor1',
                  'alarm_name': 'My alarm',
                  'new_state': 'SUBOPTIMAL'}
        result = self.vitrage_client.template.add(path=path, params=params)
        self._assert_add_result(result, LOADING_STATUS, TEMPLATE_VALIDATION_OK)

    def _delete_templates(self):
        templates = self.vitrage_client.template.list()
        template_ids = [template['uuid'] for template in templates]
        self.vitrage_client.template.delete(template_ids)


class TestTemplatesV2(TestTemplatesApis):

    def tearDown(self):
        super(TestTemplatesV2, self).tearDown()
        self._delete_templates()

    def test_templates_validate_no_type_templates(self):
        self._validate_no_type_templates(NO_TYPE_TEMPLATE)

    def test_templates_validate_standard_template(self):
        self._validate_standard_template(EXECUTE_MISTRAL_TEMPLATE)

    def test_templates_validate_definition_template(self):
        self._validate_definition_template(DEFINITION_TEMPLATE)

    def test_template_validate_with_missing_parameters(self):
        self._validate_with_missing_parameters(WITH_PARAMS_TEMPLATE)

    def test_template_validate_with_missing_parameter(self):
        self._validate_with_missing_parameter(WITH_PARAMS_TEMPLATE)

    def test_template_validate_with_parameters(self):
        self._validate_with_parameters(WITH_PARAMS_TEMPLATE)

    def test_template_add_with_missing_parameters(self):
        self._add_with_missing_parameters(WITH_PARAMS_TEMPLATE)

    def test_template_add_with_missing_parameter(self):
        self._add_with_missing_parameter(WITH_PARAMS_TEMPLATE)

    def test_template_add_with_parameters(self):
        self._add_with_parameters(WITH_PARAMS_TEMPLATE)
