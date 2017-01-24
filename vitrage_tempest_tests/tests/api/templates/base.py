# Copyright 2016 Nokia
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
import json

from oslo_log import log as logging

from vitrage import os_clients
from vitrage_tempest_tests.tests.api.base import BaseApiTest
import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)


class BaseTemplateTest(BaseApiTest):
    """Template test class for Vitrage API tests."""

    DEFAULT_PATH = '/etc/vitrage/templates/'
    TEST_PATH = '/opt/stack/vitrage/vitrage_tempest_tests/' \
                + 'tests/resources/templates/api/'

    NON_EXIST_FILE = 'non_exist_file.yaml'
    ERROR_FILE = 'corrupted_template.yaml'
    OK_FILE = 'nagios_alarm_for_alarms.yaml'

    ERROR_STATUS = 'validation failed'
    OK_STATUS = 'validation OK'
    OK_MSG = 'Template validation is OK'

    @classmethod
    def setUpClass(cls):
        super(BaseTemplateTest, cls).setUpClass()
        cls.ceilometer_client = os_clients.ceilometer_client(cls.conf)

    def _compare_template_lists(self, api_templates, cli_templates):
        self.assertNotEqual(len(api_templates), 0,
                            'The template list taken from api is empty')
        self.assertIsNotNone(cli_templates,
                             'The template list taken from cli is empty')

        LOG.info("The template list taken from cli is : " +
                 str(cli_templates))
        LOG.info("The template list taken by api is : " +
                 str(json.dumps(api_templates)))

        self._validate_templates_list_length(api_templates, cli_templates)
        self._validate_passed_templates_length(api_templates, cli_templates)
        self._compare_each_template_in_list(api_templates, cli_templates)
        self._validate_templates_existence_in_default_folder(api_templates)

    def _compare_template_validations(self, api_templates, cli_templates):
        self.assertNotEqual(len(api_templates), 0,
                            'The template validations taken from api is empty')
        self.assertIsNotNone(
            cli_templates, 'The template validations taken from cli is empty')

        LOG.info("The template validations taken from cli is : " +
                 str(cli_templates))
        LOG.info("The template validations taken by api is : " +
                 str(json.dumps(api_templates)))

        parsed_topology = json.loads(cli_templates)
        sorted_cli_templates = sorted(parsed_topology.items())
        sorted_api_templates = sorted(api_templates.items())
        self.assertEqual(sorted_api_templates, sorted_cli_templates)

    def _validate_templates_list_length(self, api_templates, cli_templates):
        self.assertEqual(len(cli_templates.splitlines()),
                         len(api_templates) + 4)

    def _validate_passed_templates_length(self, api_templates, cli_templates):
        api_passes_templates = self._filter_list_by_pairs_parameters(
            api_templates, ['status details'], [self.OK_MSG])
        cli_passes_templates = cli_templates.count(' ' + self.OK_MSG + ' ')
        self.assertEqual(cli_passes_templates, len(api_passes_templates))

    def _compare_each_template_in_list(self, api_templates, cli_templates):
        counter = 0
        for api_item in api_templates:
            for line in cli_templates.splitlines():
                name_start = line.count(' ' + api_item['name'] + ' ')
                status_start = line.count(' ' + api_item['status'] + ' ')
                if name_start > 0 and status_start > 0:
                    counter += 1
                    break
        self.assertEqual(counter, len(api_templates))

    def _validate_templates_existence_in_default_folder(self, templates_list):
        counter = 0
        text_out = utils.get_from_terminal('ls ' + self.DEFAULT_PATH)
        for item in templates_list:
            name_start = text_out.count(' ' + item['name'] + ' ')
            if name_start > -1:
                counter += 1
        self.assertEqual(counter, len(templates_list))

    def _run_default_template_validation(
            self, template, validation, path):
        self.assertNotEqual(len(validation), 0,
                            'The template validation is empty')
        self.assertEqual(validation['file path'], path)
        self.assertEqual(validation['status code'], 0)
        self.assertEqual(validation['status'], self.OK_STATUS)
        self.assertEqual(validation['message'], self.OK_MSG)
        self.assertEqual(validation['message'], template['status details'])

    def _run_template_validation(
            self, validation, path, negative=False):
        self.assertIn(path, validation['file path'])

        if negative:
            self.assertEqual(validation['status code'], 3)
            self.assertEqual(validation['status'], self.ERROR_STATUS)
            self.assertNotEqual(validation['message'], self.OK_MSG)
            return

        self.assertEqual(validation['status code'], 0)
        self.assertEqual(validation['status'], self.OK_STATUS)
        self.assertEqual(validation['message'], self.OK_MSG)

    def _compare_template_show(self, api_templates, cli_templates):
        self.assertNotEqual(len(api_templates), 0,
                            'The template validations taken from api is empty')
        self.assertIsNotNone(
            cli_templates, 'The template validations taken from cli is empty')

        LOG.info("The template validations taken from cli is : " +
                 str(cli_templates))
        LOG.info("The template validations taken by api is : " +
                 str(json.dumps(api_templates)))

        parsed_topology = json.loads(cli_templates)
        sorted_cli_templates = sorted(parsed_topology.items())
        sorted_api_templates = sorted(api_templates.items())
        self.assertEqual(sorted_api_templates, sorted_cli_templates)

    def _validate_template_structure(self, template_item, template_show):
        self.assertEqual(
            template_item['name'], template_show['metadata']['name'])
        template_content = utils.get_from_terminal(
            'cat ' + self.DEFAULT_PATH + template_item['name'] + '*')

        entities = template_content.count('entity:')
        relationships = template_content.count('relationship:')
        scenarios = template_content.count('scenario:')

        self.assertIn(
            template_show['metadata']['name'], template_content)
        self.assertEqual(
            len(template_show['definitions']['entities']), entities)
        self.assertEqual(
            len(template_show['definitions']['relationships']), relationships)
        self.assertEqual(
            len(template_show['scenarios']), scenarios)
