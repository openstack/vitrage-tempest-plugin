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
import time

from oslo_log import log as logging

from vitrage.common.constants import EntityCategory
from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources.doctor import DOCTOR_DATASOURCE
from vitrage.evaluator.actions.evaluator_event_transformer import \
    VITRAGE_DATASOURCE
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common import nova_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils
from vitrage_tempest_plugin.tests.e2e.test_actions_base import TestActionsBase
from vitrage_tempest_plugin.tests import utils

LOG = logging.getLogger(__name__)

TRIGGER_ALARM_1 = 'e2e.test_basic_actions.trigger.alarm1'
TRIGGER_ALARM_2 = 'e2e.test_basic_actions.trigger.alarm2'
TRIGGER_ALARM_3 = 'e2e.test_basic_actions.trigger.alarm3'
TRIGGER_ALARM_4 = 'e2e.test_basic_actions.trigger.alarm4'
DEDUCED = 'e2e.test_basic_actions.deduced.alarm'

TRIGGER_ALARM_2_PROPS = {
    VProps.NAME: TRIGGER_ALARM_2,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: DOCTOR_DATASOURCE,
}

DEDUCED_PROPS = {
    VProps.NAME: DEDUCED,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: VITRAGE_DATASOURCE,
}


class TestBasicActions(TestActionsBase):
    @classmethod
    def setUpClass(cls):
        super(TestBasicActions, cls).setUpClass()
        cls._template = v_utils.add_template("e2e_test_basic_actions.yaml")

    def setUp(self):
        super(TestBasicActions, self).setUp()

    def tearDown(self):
        super(TestBasicActions, self).tearDown()

    @classmethod
    def tearDownClass(cls):
        if cls._template is not None:
            v_utils.delete_template(cls._template['uuid'])

    @utils.tempest_logger
    def test_action_set_state_host(self):
        try:

            # Do
            self._trigger_do_action(TRIGGER_ALARM_1)
            curr_host = v_utils.get_first_host()
            self.assertEqual(
                'ERROR',
                curr_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after set_state action')

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_1)
            curr_host = v_utils.get_first_host()
            self.assertEqual(
                self.orig_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                curr_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after undo set_state action')
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._trigger_undo_action(TRIGGER_ALARM_1)

    @utils.tempest_logger
    def test_action_set_state_instance(self):

        vm_id = ""
        try:
            vm_id = nova_utils.create_instances(set_public_network=True)[0].id

            # Do
            orig_instance = v_utils.get_first_instance(id=vm_id)
            self._trigger_do_action(TRIGGER_ALARM_3)
            curr_instance = v_utils.get_first_instance(id=vm_id)
            self.assertEqual(
                'ERROR',
                curr_instance.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after set_state action')

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_3)
            curr_instance = v_utils.get_first_instance(id=vm_id)
            self.assertEqual(
                orig_instance.get(VProps.VITRAGE_AGGREGATED_STATE),
                curr_instance.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after undo set_state action')
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._trigger_undo_action(TRIGGER_ALARM_3)
            nova_utils.delete_all_instances(id=vm_id)

    @utils.tempest_logger
    def test_action_mark_down_host(self):
        try:
            host_name = self.orig_host.get(VProps.NAME)

            # Do
            self._trigger_do_action(TRIGGER_ALARM_4)
            nova_service = TempestClients.nova().services.list(
                host=host_name, binary='nova-compute')[0]
            self.assertEqual("down", str(nova_service.state))

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_4)
            nova_service = TempestClients.nova().services.list(
                host=host_name, binary='nova-compute')[0]
            self.assertEqual("up", str(nova_service.state))
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._trigger_undo_action(TRIGGER_ALARM_4)
            # nova.host datasource may take up to snapshot_intreval to update
            time.sleep(130)

    @utils.tempest_logger
    def test_action_mark_down_instance(self):
        vm_id = ""
        try:
            vm_id = nova_utils.create_instances(set_public_network=True)[0].id
            # Do
            self._trigger_do_action(TRIGGER_ALARM_3)
            nova_instance = TempestClients.nova().servers.get(vm_id)
            self.assertEqual("ERROR", str(nova_instance.status))

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_3)
            nova_instance = TempestClients.nova().servers.get(vm_id)
            self.assertEqual("ACTIVE", str(nova_instance.status))
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            pass
            self._trigger_undo_action(TRIGGER_ALARM_3)
            nova_utils.delete_all_instances(id=vm_id)

    @utils.tempest_logger
    def test_action_deduce_alarm(self):
        try:
            host_id = self.orig_host.get(VProps.VITRAGE_ID)

            # Do
            self._trigger_do_action(TRIGGER_ALARM_2)
            self._check_deduced(1, DEDUCED_PROPS, host_id)

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_2)
            self._check_deduced(0, DEDUCED_PROPS, host_id)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._trigger_undo_action(TRIGGER_ALARM_2)

    @utils.tempest_logger
    def test_action_add_causal_relationship(self):
        try:
            # Do
            self._trigger_do_action(TRIGGER_ALARM_2)
            alarms = TempestClients.vitrage().alarm.list(
                vitrage_id=self.orig_host.get(VProps.VITRAGE_ID),
                all_tenants=True)
            self.assertTrue(len(alarms) >= 2, 'alarms %s' % str(alarms))

            deduced = g_utils.first_match(alarms, **DEDUCED_PROPS)
            trigger = g_utils.first_match(alarms, **TRIGGER_ALARM_2_PROPS)

            # Get Rca for the deduced
            rca = TempestClients.vitrage().rca.get(
                deduced[VProps.VITRAGE_ID], all_tenants=True)
            self._check_rca(rca, [deduced, trigger], DEDUCED_PROPS)

            # Get Rca for the trigger
            rca = TempestClients.vitrage().rca.get(
                trigger[VProps.VITRAGE_ID], all_tenants=True)
            self._check_rca(rca, [deduced, trigger], TRIGGER_ALARM_2_PROPS)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._trigger_undo_action(TRIGGER_ALARM_2)
