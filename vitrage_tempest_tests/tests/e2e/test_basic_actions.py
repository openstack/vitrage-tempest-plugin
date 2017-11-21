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
from vitrage_tempest_tests.tests.base import BaseVitrageTempest
from vitrage_tempest_tests.tests.common import general_utils as g_utils
from vitrage_tempest_tests.tests.common.tempest_clients import TempestClients
from vitrage_tempest_tests.tests.common import vitrage_utils
from vitrage_tempest_tests.tests import utils

LOG = logging.getLogger(__name__)

TRIGGER_ALARM_1 = 'e2e.test_basic_actions.trigger.alarm1'
TRIGGER_ALARM_2 = 'e2e.test_basic_actions.trigger.alarm2'
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


class TestBasicActions(BaseVitrageTempest):
    @classmethod
    def setUpClass(cls):
        super(TestBasicActions, cls).setUpClass()
        host = vitrage_utils.get_first_host()
        if not host:
            raise Exception("No host found")
        if not host.get(VProps.VITRAGE_AGGREGATED_STATE) == 'AVAILABLE':
            raise Exception("Host is not running %s", str(host))
        cls.orig_host = host

    def _trigger_do_action(self, trigger_name):
        vitrage_utils.generate_fake_host_alarm(
            self.orig_host.get('name'),
            enabled=True,
            event_type=trigger_name
        )
        time.sleep(2)

    def _trigger_undo_action(self, trigger_name):
        vitrage_utils.generate_fake_host_alarm(
            self.orig_host.get('name'),
            enabled=False,
            event_type=trigger_name
        )
        time.sleep(2)

    @utils.tempest_logger
    def test_action_set_state(self):
        try:

            # Do
            self._trigger_do_action(TRIGGER_ALARM_1)
            curr_host = vitrage_utils.get_first_host()
            self.assertEqual(
                'ERROR',
                curr_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after set_state action')

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_1)
            curr_host = vitrage_utils.get_first_host()
            self.assertEqual(
                self.orig_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                curr_host.get(VProps.VITRAGE_AGGREGATED_STATE),
                'state should change after set_state action')
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._trigger_undo_action(TRIGGER_ALARM_1)

    @utils.tempest_logger
    def test_action_mark_down_host(self):
        try:
            host_name = self.orig_host.get(VProps.NAME)

            # Do
            self._trigger_do_action(TRIGGER_ALARM_1)
            nova_service = TempestClients.nova().services.list(
                host=host_name, binary='nova-compute')[0]
            self.assertEqual("down", str(nova_service.state))

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_1)
            nova_service = TempestClients.nova().services.list(
                host=host_name, binary='nova-compute')[0]
            self.assertEqual("up", str(nova_service.state))
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._trigger_undo_action(TRIGGER_ALARM_1)

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

    def _check_deduced(self, deduced_count, deduced_props, resource_id):
        alarms = TempestClients.vitrage().alarm.list(
            vitrage_id=resource_id,
            all_tenants=True)
        deduces = g_utils.get_all_matchs(alarms, deduced_props)
        self.assertEqual(
            deduced_count,
            len(deduces),
            'Expected %s deduces\n - \n%s\n - \n%s' %
            (str(deduced_count), str(alarms), str(deduces)))

    @utils.tempest_logger
    def test_action_add_causal_relationship(self):
        try:
            # Do
            self._trigger_do_action(TRIGGER_ALARM_2)
            alarms = TempestClients.vitrage().alarm.list(
                vitrage_id=self.orig_host.get(VProps.VITRAGE_ID),
                all_tenants=True)

            deduced = g_utils.get_all_matchs(alarms, DEDUCED_PROPS)[0]
            trigger = g_utils.get_all_matchs(alarms, TRIGGER_ALARM_2_PROPS)[0]

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

    def _check_rca(self, rca, expected_alarms, inspected):
        self.assertEqual(len(expected_alarms), len(rca['nodes']))
        for expected_alarm in expected_alarms:
            self.assertIsNotNone(
                g_utils.get_first_match(rca['nodes'], expected_alarm),
                'expected_alarm is not in the rca %s' % str(expected_alarm))
        rca_inspected = rca['nodes'][rca['inspected_index']]
        self.assertEqual(
            True,
            g_utils.is_subset(inspected, rca_inspected),
            'Invalid inspected item \n%s\n%s' %
            (str(rca_inspected), str(inspected)))
