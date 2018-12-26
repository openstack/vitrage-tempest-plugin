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
from testtools import matchers

from vitrage.common.exception import VitrageError
from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrage_tempest_plugin.tests.base import IsNotEmpty
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common import vitrage_utils


LOG = logging.getLogger(__name__)


class BaseTemplateTest(BaseVitrageTempest):
    """Template test class for Vitrage API tests."""

    TEST_PATH = '/opt/stack/vitrage/vitrage_tempest_plugin/' \
                + 'tests/resources/templates/api/'

    NON_EXIST_FILE = 'non_exist_file.yaml'
    ERROR_FILE = 'corrupted_template.yaml'
    OK_FILE = 'nagios_alarm_for_alarms.yaml'

    ERROR_STATUS = 'validation failed'
    OK_STATUS = 'validation OK'
    OK_MSG = 'Template validation is OK'

    def _compare_template_lists(self, api_templates, cli_templates):
        self.assertThat(api_templates, IsNotEmpty(),
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

    def _compare_template_validations(self, api_templates, cli_templates):
        self.assertThat(api_templates, IsNotEmpty(),
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
        api_passes_templates = g_utils.all_matches(
            api_templates,
            **{'status details': self.OK_MSG})
        cli_passes_templates = cli_templates.count(' ' + self.OK_MSG + ' ')
        self.assertThat(api_passes_templates,
                        matchers.HasLength(cli_passes_templates))

    def _compare_each_template_in_list(self, api_templates, cli_templates):
        counter = 0
        for api_item in api_templates:
            for line in cli_templates.splitlines():
                name_start = line.count(' ' + api_item['name'] + ' ')
                status_start = line.count(' ' + api_item['status'] + ' ')
                if name_start > 0 and status_start > 0:
                    counter += 1
                    break
        self.assertThat(api_templates, matchers.HasLength(counter))

    def _run_default_template_validation(
            self, template, validation, path):
        self.assertThat(validation, IsNotEmpty(),
                        'The template validation is empty')
        self.assertEqual(path, validation['file path'])
        self.assertEqual(0, validation['status code'])
        self.assertEqual(self.OK_STATUS, validation['status'])
        self.assertEqual(self.OK_MSG, validation['message'])
        self.assertEqual(validation['message'], template['status details'])

    def _run_template_validation(
            self, validation, path, negative=False):
        self.assertIn(path, validation['file path'])

        if negative:
            self.assertEqual(3, validation['status code'])
            self.assertEqual(self.ERROR_STATUS, validation['status'])
            self.assertNotEqual(validation['message'], self.OK_MSG)
            return

        self.assertEqual(0, validation['status code'])
        self.assertEqual(self.OK_STATUS, validation['status'])
        self.assertEqual(self.OK_MSG, validation['message'])

    def _compare_template_show(self, api_templates, cli_templates):
        self.assertThat(api_templates, IsNotEmpty(),
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

    def _rollback_to_default(self, templates):
        try:
            for t in templates:
                db_row = vitrage_utils.get_first_template(name=t)
                vitrage_utils.delete_template(db_row['uuid'])
        except Exception as e:
            raise VitrageError('Rollback to default failed %s', e)
