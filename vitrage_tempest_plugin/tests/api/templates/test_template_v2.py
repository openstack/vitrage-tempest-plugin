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

FAKE_UUID = 'ade68276-0fe9-42cd-9ec2-e7f20470a771'


class TestValidateV2(BaseTemplateTest):
    """Template test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestValidateV2, cls).setUpClass()

    def test_templates_validate_no_type_templates(self):
        try:
            path = self.TEST_PATH + NO_TYPE_TEMPLATE
            validation = self.vitrage_client.template.validate(path=path)
            self.assertEqual(1, len(validation['results']))
            self._run_template_validation(
                validation['results'][0], path, negative=True)
        except Exception:
            LOG.error('Failed to get validation of corrupted template file')

    def test_templates_validate_standard_template(self):
        try:
            path = self.TEST_PATH + EXECUTE_MISTRAL_TEMPLATE
            validation = self.vitrage_client.template.validate(path=path)
            self.assertEqual(1, len(validation['results']))
            self._run_template_validation(
                validation['results'][0], path)
        except Exception:
            LOG.error('Failed to get validation of standard template file')

    def test_templates_validate_definition_template(self):
        try:
            path = self.TEST_PATH + DEFINITION_TEMPLATE
            validation = self.vitrage_client.template.validate(path=path)
            self.assertEqual(1, len(validation['results']))
            self._run_template_validation(
                validation['results'][0], path)
        except Exception:
            LOG.error('Failed to get validation of definition template file')
