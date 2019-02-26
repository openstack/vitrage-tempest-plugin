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

from vitrage_tempest_plugin.tests.common.constants import DOCTOR_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import EntityCategory
from vitrage_tempest_plugin.tests.common.constants import VertexProperties \
    as VProps
from vitrage_tempest_plugin.tests.common.constants import VITRAGE_DATASOURCE
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
TRIGGER_ALARM_5 = 'e2e.test_basic_actions.trigger.alarm5'
DEDUCED = 'e2e.test_basic_actions.deduced.alarm'

TRIGGER_ALARM_1_V3 = 'e2e.test_basic_actions.trigger.alarm1.v3'
TRIGGER_ALARM_2_V3 = 'e2e.test_basic_actions.trigger.alarm2.v3'
TRIGGER_ALARM_3_V3 = 'e2e.test_basic_actions.trigger.alarm3.v3'
TRIGGER_ALARM_4_V3 = 'e2e.test_basic_actions.trigger.alarm4.v3'
TRIGGER_ALARM_5_V3 = 'e2e.test_basic_actions.trigger.alarm5.v3'
TRIGGER_ALARM_6_V3 = 'e2e.test_basic_actions.trigger.alarm6.v3'
DEDUCED_V3 = 'e2e.test_basic_actions.deduced.alarm.v3'

TRIGGER_ALARM_2_PROPS = {
    VProps.NAME: TRIGGER_ALARM_2,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: DOCTOR_DATASOURCE,
}

TRIGGER_ALARM_2_PROPS_V3 = {
    VProps.NAME: TRIGGER_ALARM_2_V3,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: DOCTOR_DATASOURCE,
}

TRIGGER_ALARM_6_PROPS_V3 = {
    VProps.NAME: TRIGGER_ALARM_6_V3,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: DOCTOR_DATASOURCE,
}

DEDUCED_PROPS = {
    VProps.NAME: DEDUCED,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: VITRAGE_DATASOURCE,
}

DEDUCED_PROPS_V3 = {
    VProps.NAME: DEDUCED_V3,
    VProps.VITRAGE_CATEGORY: EntityCategory.ALARM,
    VProps.VITRAGE_TYPE: VITRAGE_DATASOURCE,
}


class TestBasicActions(TestActionsBase):
    @classmethod
    def setUpClass(cls):
        super(TestBasicActions, cls).setUpClass()
        cls._templates = []
        cls._templates.append(
            v_utils.add_template("e2e_test_basic_actions.yaml"))
        cls._templates.append(
            v_utils.add_template("e2e_test_basic_actions_v3.yaml"))

    @classmethod
    def tearDownClass(cls):
        for t in cls._templates:
            v_utils.delete_template(t['uuid'])

    @utils.tempest_logger
    def test_action_set_state_host(self):
        self._do_test_action_set_state_host(TRIGGER_ALARM_1)

    @utils.tempest_logger
    def test_action_set_state_host_v3(self):
        self._do_test_action_set_state_host(TRIGGER_ALARM_1_V3)

    def _do_test_action_set_state_host(self, trigger_name):
        try:

            # Do
            self._trigger_do_action(trigger_name)
            curr_host = v_utils.get_first_host()
            self.assertEqual(
                'ERROR',
                curr_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after set_state action')

            # Undo
            self._trigger_undo_action(trigger_name)
            curr_host = v_utils.get_first_host()
            self.assertEqual(
                self.orig_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                curr_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after undo set_state action')
        finally:
            self._trigger_undo_action(trigger_name)

    @utils.tempest_logger
    def test_action_set_state_instance(self):
        self._do_test_action_set_state_instance(TRIGGER_ALARM_3)

    @utils.tempest_logger
    def test_action_set_state_instance_v3(self):
        self._do_test_action_set_state_instance(TRIGGER_ALARM_3_V3)

    def _do_test_action_set_state_instance(self, trigger_name):

        vm_id = ""
        try:
            vm_id = nova_utils.create_instances(set_public_network=True)[0].id

            # Do
            orig_instance = v_utils.get_first_instance(id=vm_id)
            self._trigger_do_action(trigger_name)
            curr_instance = v_utils.get_first_instance(id=vm_id)
            self.assertEqual(
                'ERROR',
                curr_instance.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after set_state action')

            # Undo
            self._trigger_undo_action(trigger_name)
            curr_instance = v_utils.get_first_instance(id=vm_id)
            self.assertEqual(
                orig_instance.get(VProps.VITRAGE_AGGREGATED_STATE),
                curr_instance.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after undo set_state action')
        finally:
            self._trigger_undo_action(trigger_name)
            nova_utils.delete_all_instances(id=vm_id)

    @utils.tempest_logger
    def test_action_mark_down_host(self):
        self._do_test_action_mark_down_host(TRIGGER_ALARM_4)

    @utils.tempest_logger
    def test_action_mark_down_host_v3(self):
        self._do_test_action_mark_down_host(TRIGGER_ALARM_4_V3)

    def _do_test_action_mark_down_host(self, trigger_name):
        try:
            host_name = self.orig_host.get(VProps.NAME)

            # Do
            self._trigger_do_action(trigger_name)
            nova_service = TempestClients.nova().services.list(
                host=host_name, binary='nova-compute')[0]
            self.assertEqual("down", nova_service.state)

            # Undo
            self._trigger_undo_action(trigger_name)
            nova_service = TempestClients.nova().services.list(
                host=host_name, binary='nova-compute')[0]
            self.assertEqual("up", nova_service.state)
        finally:
            self._trigger_undo_action(trigger_name)
            # nova.host datasource may take up to snapshot_intreval to update
            time.sleep(130)

    @utils.tempest_logger
    def test_action_mark_down_instance(self):
        self._do_test_action_mark_down_instance(TRIGGER_ALARM_5)

    @utils.tempest_logger
    def test_action_mark_down_instance_v3(self):
        self._do_test_action_mark_down_instance(TRIGGER_ALARM_5_V3)

    def _do_test_action_mark_down_instance(self, trigger_name):
        vm_id = ""
        try:
            vm_id = nova_utils.create_instances(set_public_network=True)[0].id
            # Do
            self._trigger_do_action(trigger_name)
            nova_instance = TempestClients.nova().servers.get(vm_id)
            self.assertEqual("ERROR", nova_instance.status)

            # Undo
            self._trigger_undo_action(trigger_name)
            nova_instance = TempestClients.nova().servers.get(vm_id)
            self.assertEqual("ACTIVE", nova_instance.status)
        finally:
            self._trigger_undo_action(trigger_name)
            nova_utils.delete_all_instances(id=vm_id)

    @utils.tempest_logger
    def test_action_deduce_alarm(self):
        self._do_test_action_deduce_alarm(TRIGGER_ALARM_2, DEDUCED_PROPS)

    @utils.tempest_logger
    def test_action_deduce_alarm_v3(self):
        self._do_test_action_deduce_alarm(TRIGGER_ALARM_2_V3, DEDUCED_PROPS_V3)

    def _do_test_action_deduce_alarm(self, trigger_name, deduced_props):
        try:
            host_id = self.orig_host.get(VProps.VITRAGE_ID)

            # Do
            self._trigger_do_action(trigger_name)
            self._check_deduced(1, deduced_props, host_id)

            # Undo
            self._trigger_undo_action(trigger_name)
            self._check_deduced(0, deduced_props, host_id)
        finally:
            self._trigger_undo_action(trigger_name)

    @utils.tempest_logger
    def test_action_add_causal_relationship(self):
        self._do_test_action_add_causal_relationship(TRIGGER_ALARM_2,
                                                     DEDUCED_PROPS,
                                                     TRIGGER_ALARM_2_PROPS)

    @utils.tempest_logger
    def test_action_add_causal_relationship_v3(self):
        self._do_test_action_add_causal_relationship(TRIGGER_ALARM_2_V3,
                                                     DEDUCED_PROPS_V3,
                                                     TRIGGER_ALARM_2_PROPS_V3)

    @utils.tempest_logger
    def test_action_add_raise_alarm_with_causing_alarm(self):
        self._do_test_action_add_causal_relationship(TRIGGER_ALARM_6_V3,
                                                     DEDUCED_PROPS_V3,
                                                     TRIGGER_ALARM_6_PROPS_V3)

    def _do_test_action_add_causal_relationship(self,
                                                trigger_name,
                                                deduced_props,
                                                trigger_alarm_props):
        try:
            # Do
            self._trigger_do_action(trigger_name)
            alarms = self.vitrage_client.alarm.list(
                vitrage_id=self.orig_host.get(VProps.VITRAGE_ID),
                all_tenants=True)
            self.assertTrue(len(alarms) >= 2, 'alarms %s' % alarms)

            deduced = g_utils.first_match(alarms, **deduced_props)
            trigger = g_utils.first_match(alarms, **trigger_alarm_props)

            # Get Rca for the deduced
            rca = self.vitrage_client.rca.get(deduced[VProps.VITRAGE_ID],
                                              all_tenants=True)
            self._check_rca(rca, [deduced, trigger], deduced_props)

            # Get Rca for the trigger
            rca = self.vitrage_client.rca.get(trigger[VProps.VITRAGE_ID],
                                              all_tenants=True)
            self._check_rca(rca, [deduced, trigger], trigger_alarm_props)
        finally:
            self._trigger_undo_action(trigger_name)
