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
from oslo_log import log as logging
import time

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.evaluator.actions.evaluator_event_transformer import \
    VITRAGE_DATASOURCE
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_util
from vitrage_tempest_plugin.tests.e2e.test_actions_base import TestActionsBase
from vitrage_tempest_plugin.tests import utils

LOG = logging.getLogger(__name__)

TRIGGER_ALARM_1 = 'e2e.test_template_actions.trigger.alarm1'
DEDUCED = 'e2e.test_template_actions.deduced.alarm'

TRIGGER_ALARM_2 = 'e2e.test_template_actions.trigger.alarm2'
DEDUCED_2 = 'e2e.test_template_actions.deduced.alarm2'

TEST_TEMPLATE = 'e2e_test_template_actions.yaml'
TEST_TEMPLATE_2 = 'e2e_test_template_actions_2.yaml'

INFILE_NAME = 'e2e_test_template_actions'
INFILE_NAME_2 = 'e2e_test_template_actions_2'


FOLDER_PATH = 'templates/api/e2e_test_template'

DEDUCED_PROPS = {
    VProps.NAME: DEDUCED,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: VITRAGE_DATASOURCE,
}

DEDUCED_PROPS_2 = {
    VProps.NAME: DEDUCED_2,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: VITRAGE_DATASOURCE,
}


class TestTemplateActions(TestActionsBase):

    def __init__(self, *args, **kwds):
        super(TestTemplateActions, self).__init__(*args, **kwds)
        self.added_template = None

    def setUp(self):
        super(TestTemplateActions, self).setUp()

    def tearDown(self):
        super(TestTemplateActions, self).tearDown()
        time.sleep(10)
        self._trigger_undo_action(TRIGGER_ALARM_1)
        if self.added_template is not None:
            v_util.delete_template(self.added_template['uuid'])
            self.added_template = None

    @utils.tempest_logger
    def test_evaluator_reload_with_new_template(self):
        """Test reload new template e2e

        1. raise trigger alarm (template is not loaded yet)
        2. add the relevant template
        3. check action is executed
        This checks that the evaluators are reloaded and run on all existing
         vertices.
        """
        try:
            host_id = self.orig_host.get(VProps.VITRAGE_ID)
            self._trigger_do_action(TRIGGER_ALARM_1)
            self.added_template = v_util.add_template(TEST_TEMPLATE,
                                                      folder=FOLDER_PATH)
            self._check_deduced(1, DEDUCED_PROPS, host_id)

        except Exception as e:
            self._handle_exception(e)
            raise

    @utils.tempest_logger
    def test_evaluator_reload_with_existing_template(self):
        """Test reload new template e2e

        1.add the relevant template
        2.raise trigger alarm.
        3. check action is executed
        This checks that new workers execute new template
        """
        try:
            host_id = self.orig_host.get(VProps.VITRAGE_ID)
            self.added_template = v_util.add_template(TEST_TEMPLATE,
                                                      folder=FOLDER_PATH)
            self._trigger_do_action(TRIGGER_ALARM_1)
            self._check_deduced(1, DEDUCED_PROPS, host_id)

        except Exception as e:
            self._handle_exception(e)
            raise

    @utils.tempest_logger
    def test_evaluator_reload_with_new_template_v2(self):
        """Test reload new template e2e v2

        1. raise trigger alarm
        2. add the relevant template
        3. delete the template.
        4. check action - should be not active.
        This checks that the evaluators are reloaded and run on all existing
         vertices.
         Checks temporary worker that was added to delete template.
        """
        try:
            host_id = self.orig_host.get(VProps.VITRAGE_ID)

            self._trigger_do_action(TRIGGER_ALARM_1)
            self.added_template = v_util.add_template(TEST_TEMPLATE,
                                                      folder=FOLDER_PATH)
            self._check_deduced(1, DEDUCED_PROPS, host_id)
            v_util.delete_template(self.added_template['uuid'])
            self.added_template = None
            self._check_deduced(0, DEDUCED_PROPS, host_id)

        except Exception as e:
            self._handle_exception(e)
            raise

    @utils.tempest_logger
    def test_evaluator_reload_with_existing_template_v2(self):
        """Test reload new template e2e v2

        1.add the relevant template
        2.delete the template
        2.raise trigger alarm.
        3. check no deduced alarm
        This checks that template deleted properly and no action executed.
        :return:
        """
        try:
            host_id = self.orig_host.get(VProps.VITRAGE_ID)
            self.added_template = v_util.add_template(TEST_TEMPLATE,
                                                      folder=FOLDER_PATH)
            v_util.delete_template(self.added_template['uuid'])
            self.added_template = None
            self._trigger_do_action(TRIGGER_ALARM_1)
            self._check_deduced(0, DEDUCED_PROPS, host_id)

        except Exception as e:
            self._handle_exception(e)
            raise

    @utils.tempest_logger
    def test_evaluator_reload_with_multiple_new_template(self):
        """Test reload new template e2e

        1. raise trigger alarm (template is not loaded yet)
        2. add 2 new templates.
        3. check both actions are executed
        This checks that the evaluators are reloaded for both templates
         and run on all existing vertices.
        """
        try:
            host_id = self.orig_host.get(VProps.VITRAGE_ID)
            self._trigger_do_action(TRIGGER_ALARM_1)
            self._trigger_do_action(TRIGGER_ALARM_2)
            v_util.add_template(folder=FOLDER_PATH)
            self.added_template = v_util.get_first_template(name=INFILE_NAME)
            second_template = v_util.get_first_template(name=INFILE_NAME_2)
            self._check_deduced(1, DEDUCED_PROPS, host_id)
            self._check_deduced(1, DEDUCED_PROPS_2, host_id)

        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            if second_template:
                v_util.delete_template(second_template['uuid'])
