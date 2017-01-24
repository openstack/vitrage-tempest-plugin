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

from vitrage_tempest_tests.tests.api.templates.base import BaseTemplateTest
import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)


class TestValidate(BaseTemplateTest):
    """Template test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestValidate, cls).setUpClass()

    def test_templates_list(self):
        """template_list test

        There test validate correctness of template list,
        compare templates files existence with default folder
        and between cli via api ...
        """
        api_template_list = self.vitrage_client.template.list()
        cli_template_list = utils.run_vitrage_command(
            'vitrage template list', self.conf)

        self._compare_template_lists(api_template_list, cli_template_list)

    def test_compare_templates_validation(self):
        """template_validate test

        There test validate correctness of template validation,
        compare templates files validation between cli via api
        """
        path = self.DEFAULT_PATH
        api_template_validation = \
            self.vitrage_client.template.validate(path=path)
        cli_template_validation = utils.run_vitrage_command(
            'vitrage template validate --path ' + path, self.conf)

        self._compare_template_validations(
            api_template_validation, cli_template_validation)

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
            self.assertEqual(up.strerror, 'No such file or directory')
            self.assertEqual(up.errno, 2)

    def test_templates_validate_corrupted_templates(self):
        """templates_validate test

        There negative test - validate correctness of error
        message in case of corrupted template file
        """
        try:
            path = self.TEST_PATH + self.ERROR_FILE
            validation = self.vitrage_client.template.validate(path=path)
            self.assertEqual(len(validation['results']), 1)
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
            self.assertEqual(len(validation['results']), 1)
            self._run_template_validation(
                validation['results'][0], path)
        except Exception:
            LOG.error('Failed to get validation of template file')

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
