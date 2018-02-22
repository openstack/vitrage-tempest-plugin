# Copyright 2016 - Nokia
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

import unittest

from oslo_log import log as logging

from vitrage.common.constants import TemplateStatus
from vitrage.common.constants import TemplateTypes as TTypes
from vitrage.utils import file
from vitrage_tempest_plugin.tests.api.templates.base import BaseTemplateTest
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils
import vitrage_tempest_plugin.tests.utils as utils

LOG = logging.getLogger(__name__)

STANDARD_TEMPLATE = 'host_high_memory_usage_scenarios.yaml'
EQUIVALENCE_TEMPLATE = 'basic_equivalence_templates.yaml'
DEFINITION_TEMPLATE = 'basic_def_template.yaml'
STANDARD_ERROR = 'corrupted_template.yaml'

FAKE_UUID = 'ade68276-0fe9-42cd-9ec2-e7f20470a771'


class TestValidate(BaseTemplateTest):
    """Template test class for Vitrage API tests."""

    def setUp(self):
        super(TestValidate, self).setUp()

    def tearDown(self):
        super(TestValidate, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestValidate, cls).setUpClass()
        cls._template = v_utils.add_template(STANDARD_TEMPLATE)

    @classmethod
    def tearDownClass(cls):
        if cls._template is not None:
            v_utils.delete_template(cls._template['uuid'])

    def test_templates_list(self):
        """template_list test

        There test validate correctness of template list,
        equals templates files existence with default folder
        and between cli via api ...
        """
        api_template_list = self.vitrage_client.template.list()
        cli_template_list = utils.run_vitrage_command(
            'vitrage template list', self.conf)

        self._compare_template_lists(api_template_list, cli_template_list)

    def test_compare_templates_validation(self):
        """template_validate test

        There test validate correctness of template validation,
        equals templates files validation between cli via api
        """
        path = self.DEFAULT_PATH
        api_template_validation = \
            self.vitrage_client.template.validate(path=path)
        cli_template_validation = utils.run_vitrage_command(
            'vitrage template validate --path ' + path, self.conf)

        self._compare_template_validations(
            api_template_validation, cli_template_validation)

    @unittest.skip("skipping test")
    # TODO(nivo): fix test - passes on machine but not at gate
    def test_templates_validate_default_templates(self):
        """templates_validate test

        There test validate correctness of list of uploaded template files
        (in /etc/vitrage/templates folder)
        """
        path = self.DEFAULT_PATH
        validation = self.vitrage_client.template.validate(path=path)
        self.assertNotEqual(len(validation), 0)
        for item in validation['results']:
            self._run_template_validation(item, path)

    def test_templates_validate_non_exist_template(self):
        """templates_validate test

        There negative test - validate error message
         in case of non-exist template file
        """
        try:
            path = self.TEST_PATH + self.NON_EXIST_FILE
            validation = self.vitrage_client.template.validate(path=path)
            self.assertIsNone(validation)
        except Exception as up:
            self.assertEqual('No such file or directory', up.strerror)
            self.assertEqual(2, up.errno)

    def test_templates_validate_corrupted_templates(self):
        """templates_validate test

        There negative test - validate correctness of error
        message in case of corrupted template file
        """
        try:
            path = self.TEST_PATH + self.ERROR_FILE
            validation = self.vitrage_client.template.validate(path=path)
            self.assertEqual(1, len(validation['results']))
            self._run_template_validation(
                validation['results'][0], path, negative=True)
        except Exception:
            LOG.error('Failed to get validation of corrupted template file')

    def test_templates_validate_correct_template(self):
        """templates_validate test

        There test validate correctness of template file
        """
        try:
            path = self.TEST_PATH + self.OK_FILE
            validation = self.vitrage_client.template.validate(path=path)
            self.assertEqual(1, len(validation['results']))
            self._run_template_validation(
                validation['results'][0], path)
        except Exception:
            LOG.error('Failed to get validation of template file')

    @unittest.skip("CLI tests are ineffective and not maintained")
    def test_compare_template_show(self):
        """templates_show test

        There test validate correctness of uploaded template files
        one by one with full details
        (in /etc/vitrage/templates folder)
        """
        template_list = self.vitrage_client.template.list()
        self.assertNotEqual(len(template_list), 0)
        for item in template_list:
            api_template_show = self.vitrage_client.template.show(item['uuid'])
            cli_template_show = utils.run_vitrage_command(
                'vitrage template show ' + item['uuid'], self.conf)

            self._compare_template_show(
                api_template_show, cli_template_show)
            self._validate_template_structure(item, api_template_show)


class TemplatesDBTest(BaseTemplateTest):
    """Template DB test class for vitrage API tests"""

    @classmethod
    def setUpClass(cls):
        super(TemplatesDBTest, cls).setUpClass()
        cls.client = TempestClients.vitrage()

    def test_template_add(self):
        """template add test

        test standard , definition and equivalence templates
        """
        templates_names = list()
        try:
            # TODO(ikinory): add folder of templates
            # Add standard ,equivalence and definition templates
            templates_names = self._add_templates()
            v_utils.add_template(STANDARD_TEMPLATE,
                                 template_type=TTypes.STANDARD)
            # assert standard template
            db_row = v_utils.get_first_template(
                name='host_high_memory_usage_scenarios', type=TTypes.STANDARD)
            self.assertEqual(db_row['name'],
                             'host_high_memory_usage_scenarios',
                             'standard template not found in list')

            # assert equivalence template
            db_row = v_utils.get_first_template(
                name='entity equivalence example',
                type=TTypes.EQUIVALENCE)
            self.assertEqual(db_row['name'],
                             'entity equivalence example',
                             'equivalence template not found in list')

            # assert definition template
            db_row = v_utils.get_first_template(
                name='basic_def_template',
                type=TTypes.DEFINITION,
                status=TemplateStatus.ACTIVE)

            self.assertEqual(db_row['name'],
                             'basic_def_template',
                             'definition template not found in list')

            # assert corrupted template - validate failed
            db_row = v_utils.get_first_template(
                name='corrupted_template',
                type=TTypes.STANDARD,
                status=TemplateStatus.ERROR)
            self.assertIsNotNone(
                db_row,
                'corrupted template template presented in list')

        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._rollback_to_default(templates_names)

    def test_template_delete(self):
        try:

            # add standard template
            v_utils.add_template(STANDARD_TEMPLATE,
                                 template_type=TTypes.STANDARD)
            db_row = v_utils.get_first_template(
                name='host_high_memory_usage_scenarios',
                type=TTypes.STANDARD,
                status=TemplateStatus.ACTIVE)
            self.assertIsNotNone(db_row,
                                 'Template should appear in templates list')

            # delete template
            uuid = db_row['uuid']
            v_utils.delete_template(uuid)
            db_row = v_utils.get_first_template(
                name='host_high_memory_usage_scenarios', type=TTypes.STANDARD)
            self.assertIsNone(db_row, 'Template should not appear in list')

        except Exception as e:
            self._handle_exception(e)
            raise

    def test_compare_cli_to_api(self):
        """Compare between api template list

        to cli template list
        compares each template in list
        """
        templates_names = list()
        try:
            # Add standard ,equivalence and definition templates
            templates_names = self._add_templates()
            cli_templates_list = utils.run_vitrage_command(
                "vitrage template list", self.conf)
            api_templates_list = self.client.template.list()

            self.assertNotEqual(len(api_templates_list), 0,
                                'The template list taken from api is empty')
            self.assertIsNotNone(cli_templates_list,
                                 'The template list taken from cli is empty')
            self._validate_templates_list_length(api_templates_list,
                                                 cli_templates_list)
            self._validate_passed_templates_length(api_templates_list,
                                                   cli_templates_list)
            self._compare_each_template_in_list(api_templates_list,
                                                cli_templates_list)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._rollback_to_default(templates_names)

    def test_template_show(self):
        """Compare template content from file to DB"""
        try:
            # add standard template
            template_path = \
                g_utils.tempest_resources_dir() + '/templates/api/'\
                + STANDARD_TEMPLATE
            v_utils.add_template(STANDARD_TEMPLATE,
                                 template_type=TTypes.STANDARD)
            db_row = v_utils.get_first_template(
                name='host_high_memory_usage_scenarios',
                type=TTypes.STANDARD,
                status=TemplateStatus.ACTIVE)
            payload_from_db = self.client.template.show(db_row['uuid'])
            payload_from_file = file.load_yaml_file(template_path)
            self.assertEqual(payload_from_file, payload_from_db,
                             "Template content doesn't match")
            v_utils.delete_template(db_row['uuid'])
        except Exception as e:
            self._handle_exception(e)
            raise

    def _add_templates(self):
        v_utils.add_template(STANDARD_TEMPLATE,
                             template_type=TTypes.STANDARD)
        v_utils.add_template(EQUIVALENCE_TEMPLATE,
                             template_type=TTypes.EQUIVALENCE)
        v_utils.add_template(DEFINITION_TEMPLATE,
                             template_type=TTypes.DEFINITION)
        v_utils.add_template(STANDARD_ERROR,
                             template_type=TTypes.STANDARD)
        return ['host_high_memory_usage_scenarios',
                'entity equivalence example',
                'basic_def_template',
                'corrupted_template']
