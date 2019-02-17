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


class TestTemplatesV2(BaseTemplateTest):

    """Template test class for Vitrage API tests."""
    FAILED_TO_RESOLVE_PARAM = 'Failed to resolve parameter'
    ERROR_STATUS = 'ERROR'
    LOADING_STATUS = 'LOADING'
    TEMPLATE_VALIDATION_OK = 'Template validation is OK'

    def tearDown(self):
        super(TestTemplatesV2, self).tearDown()
        self._delete_templates()

    def test_templates_validate_no_type_templates(self):
        path = self.TEST_PATH + NO_TYPE_TEMPLATE
        validation = self.vitrage_client.template.validate(path=path)
        self._assert_validate_result(
            validation, path, negative=True, status_code='')

    def test_templates_validate_standard_template(self):
        path = self.TEST_PATH + EXECUTE_MISTRAL_TEMPLATE
        validation = self.vitrage_client.template.validate(path=path)
        self._assert_validate_result(validation, path)

    def test_templates_validate_definition_template(self):
        path = self.TEST_PATH + DEFINITION_TEMPLATE
        validation = self.vitrage_client.template.validate(path=path)
        self._assert_validate_result(validation, path)

    def test_template_validate_with_missing_parameters(self):
        path = self.TEST_PATH + WITH_PARAMS_TEMPLATE
        validation = self.vitrage_client.template.validate(path=path)
        self._assert_validate_result(
            validation, path, negative=True, status_code=163)

    def test_template_validate_with_missing_parameter(self):
        path = self.TEST_PATH + WITH_PARAMS_TEMPLATE
        params = {'template_name': 'My template 1',
                  'new_state': 'SUBOPTIMAL'}
        validation = \
            self.vitrage_client.template.validate(path=path, params=params)
        self._assert_validate_result(
            validation, path, negative=True, status_code=163)

    def test_template_validate_with_parameters(self):
        path = self.TEST_PATH + WITH_PARAMS_TEMPLATE
        params = {'template_name': 'My template 1',
                  'alarm_type': 'Monitor1',
                  'alarm_name': 'My alarm',
                  'new_state': 'SUBOPTIMAL'}
        validation = \
            self.vitrage_client.template.validate(path=path, params=params)
        self._assert_validate_result(validation, path)

    def test_template_add_with_missing_parameters(self):
        path = self.TEST_PATH + WITH_PARAMS_TEMPLATE
        result = self.vitrage_client.template.add(path=path)
        self._assert_add_result(result, self.ERROR_STATUS,
                                self.FAILED_TO_RESOLVE_PARAM)

    def test_template_add_with_missing_parameter(self):
        path = self.TEST_PATH + WITH_PARAMS_TEMPLATE
        params = {'template_name': 'My template 1',
                  'new_state': 'SUBOPTIMAL'}
        result = self.vitrage_client.template.add(path=path, params=params)
        self._assert_add_result(result, self.ERROR_STATUS,
                                self.FAILED_TO_RESOLVE_PARAM)

    def test_template_add_with_parameters(self):
        path = self.TEST_PATH + WITH_PARAMS_TEMPLATE
        params = {'template_name': 'My template 1',
                  'alarm_type': 'Monitor1',
                  'alarm_name': 'My alarm',
                  'new_state': 'SUBOPTIMAL'}
        result = self.vitrage_client.template.add(path=path, params=params)
        self._assert_add_result(result, self.LOADING_STATUS,
                                self.TEMPLATE_VALIDATION_OK)

    def _delete_templates(self):
        templates = self.vitrage_client.template.list()
        template_ids = [template['uuid'] for template in templates]
        self.vitrage_client.template.delete(template_ids)
