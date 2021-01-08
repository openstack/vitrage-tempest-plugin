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
from oslo_log import log as logging
import testtools
from testtools import matchers
import yaml

from vitrage_tempest_plugin.tests.api.templates.base import BaseTemplateTest
from vitrage_tempest_plugin.tests.base import IsNotEmpty
from vitrage_tempest_plugin.tests.common.constants import TemplateStatus
from vitrage_tempest_plugin.tests.common.constants import TemplateTypes as \
    TTypes
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils

import vitrage_tempest_plugin.tests.utils as utils
from vitrageclient.exceptions import ClientException

LOG = logging.getLogger(__name__)

STANDARD_TEMPLATE = 'host_high_memory_usage_scenarios.yaml'
EQUIVALENCE_TEMPLATE = 'basic_equivalence_templates.yaml'
DEFINITION_TEMPLATE = 'basic_def_template.yaml'
STANDARD_ERROR = 'corrupted_template.yaml'

FAKE_UUID = 'ade68276-0fe9-42cd-9ec2-e7f20470a771'


class TestValidate(BaseTemplateTest):
    """Template test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestValidate, cls).setUpClass()
        cls._template = v_utils.add_template(STANDARD_TEMPLATE)

    @classmethod
    def tearDownClass(cls):
        super(TestValidate, cls).tearDownClass()
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
            'vitrage template list')

        self._compare_template_lists(api_template_list, cli_template_list)

    def test_templates_validate_non_exist_template(self):
        """templates_validate test

        There negative test - validate error message
         in case of non-exist template file
        """
        path = self.TEST_PATH + self.NON_EXIST_FILE
        self.assertRaises(IOError,
                          self.vitrage_client.template.validate,
                          path=path)

    def test_templates_validate_corrupted_templates(self):
        """templates_validate test

        There negative test - validate correctness of error
        message in case of corrupted template file
        """
        path = self.TEST_PATH + self.ERROR_FILE
        validation = self.vitrage_client.template.validate(path=path)
        self.assertThat(validation['results'], matchers.HasLength(1))
        self._assert_validate_result(validation, path,
                                     negative=True, status_code=3)

    def test_templates_validate_correct_template(self):
        """templates_validate test

        There test validate correctness of template file
        """
        path = self.TEST_PATH + self.OK_FILE
        validation = self.vitrage_client.template.validate(path=path)
        self.assertThat(validation['results'], matchers.HasLength(1))
        self._assert_validate_result(validation, path)


@testtools.skip("skip for now")
class TemplatesDBTest(BaseTemplateTest):
    """Template DB test class for vitrage API tests"""

    def test_template_add(self):
        """template add test

        test standard , definition and equivalence templates
        """
        # TODO(ikinory): add folder of templates
        # Add standard ,equivalence and definition templates
        self._add_templates()
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

    def test_template_delete(self):
        self._add_delete_template()

    def test_template_delete_with_name(self):
        self._add_delete_template_with_name()

    def test_template_dont_show_deleted_template(self):

        uuid = self._add_delete_template()
        self.assertRaises(ClientException,
                          self.vitrage_client.template.show,
                          uuid)

    def test_compare_cli_to_api(self):
        """Compare between api template list

        to cli template list
        compares each template in list
        """
        # Add standard ,equivalence and definition templates
        self._add_templates()
        cli_templates_list = utils.run_vitrage_command(
            "vitrage template list")
        api_templates_list = self.vitrage_client.template.list()

        self.assertThat(api_templates_list, IsNotEmpty(),
                        'The template list taken from api is empty')
        self.assertIsNotNone(cli_templates_list,
                             'The template list taken from cli is empty')
        self._validate_templates_list_length(api_templates_list,
                                             cli_templates_list)
        self._validate_passed_templates_length(api_templates_list,
                                               cli_templates_list)
        self._compare_each_template_in_list(api_templates_list,
                                            cli_templates_list)

    def test_template_show(self):
        """Compare template content from file to DB"""
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
        payload_from_db = self.vitrage_client.template.show(db_row['uuid'])
        with open(template_path, 'r') as stream:
            payload_from_file = yaml.load(stream, Loader=yaml.BaseLoader)
        self.assert_dict_equal(payload_from_file, payload_from_db,
                               "Template content doesn't match")
        v_utils.delete_template(db_row['uuid'])

    def test_template_show_with_name(self):
        """Compare template content from file to DB"""
        # add standard template
        template_path = \
            g_utils.tempest_resources_dir() + '/templates/api/' \
            + STANDARD_TEMPLATE
        v_utils.add_template(STANDARD_TEMPLATE,
                             template_type=TTypes.STANDARD)
        name = 'host_high_memory_usage_scenarios'
        db_row = v_utils.get_first_template(
            name=name,
            type=TTypes.STANDARD,
            status=TemplateStatus.ACTIVE)
        payload_from_db = self.vitrage_client.template.show(name)
        with open(template_path, 'r') as stream:
            payload_from_file = yaml.load(stream, Loader=yaml.BaseLoader)
        self.assert_dict_equal(payload_from_file, payload_from_db,
                               "Template content doesn't match")
        v_utils.delete_template(db_row['uuid'])

    @staticmethod
    def _add_templates():
        v_utils.add_template(STANDARD_TEMPLATE,
                             template_type=TTypes.STANDARD)
        v_utils.add_template(EQUIVALENCE_TEMPLATE,
                             template_type=TTypes.EQUIVALENCE)
        v_utils.add_template(DEFINITION_TEMPLATE,
                             template_type=TTypes.DEFINITION)
        v_utils.add_template(STANDARD_ERROR,
                             template_type=TTypes.STANDARD,
                             status=TemplateStatus.ERROR)
        return ['host_high_memory_usage_scenarios',
                'entity equivalence example',
                'basic_def_template',
                'corrupted_template']

    def _add_delete_template(self):
        """A helper function:

            Adds and deletes a template.
            Returns its uuid.
        """

        # add a template
        v_utils.add_template(STANDARD_TEMPLATE, template_type=TTypes.STANDARD)
        db_row = v_utils.get_first_template(
            name='host_high_memory_usage_scenarios',
            type=TTypes.STANDARD,
            status=TemplateStatus.ACTIVE)
        self.assertIsNotNone(db_row,
                             'Template should appear in templates list')

        # delete it
        uuid = db_row['uuid']
        v_utils.delete_template(uuid)
        db_row = v_utils.get_first_template(
            name='host_high_memory_usage_scenarios',
            type=TTypes.STANDARD)
        self.assertIsNone(db_row, 'Template should not appear in list')

        return uuid

    def _add_delete_template_with_name(self):
        """A helper function:

            Adds and deletes a template.
            Returns its name.
        """

        # add a template
        v_utils.add_template(STANDARD_TEMPLATE, template_type=TTypes.STANDARD)
        db_row = v_utils.get_first_template(
            name='host_high_memory_usage_scenarios',
            type=TTypes.STANDARD,
            status=TemplateStatus.ACTIVE)
        self.assertIsNotNone(db_row,
                             'Template should appear in templates list')

        # delete it
        name = db_row['name']
        v_utils.delete_template_with_name(name)
        db_row = v_utils.get_first_template(
            name='host_high_memory_usage_scenarios',
            type=TTypes.STANDARD)
        self.assertIsNone(db_row, 'Template should not appear in list')

        return name
