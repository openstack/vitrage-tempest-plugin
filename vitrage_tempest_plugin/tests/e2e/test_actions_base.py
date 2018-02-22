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

from vitrage.common.constants import VertexProperties as VProps
from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrage_tempest_plugin.tests.common import general_utils as g_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils

LOG = logging.getLogger(__name__)


class TestActionsBase(BaseVitrageTempest):
    def setUp(self):
        super(TestActionsBase, self).setUp()

    def tearDown(self):
        super(TestActionsBase, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestActionsBase, cls).setUpClass()
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

    def _check_deduced(self, deduced_count, deduced_props, resource_id):
        alarms = TempestClients.vitrage().alarm.list(
            vitrage_id=resource_id,
            all_tenants=True)
        deduces = g_utils.all_matches(alarms, **deduced_props)
        self.assertEqual(
            deduced_count,
            len(deduces),
            'Expected %s deduces\n - \n%s\n - \n%s' %
            (str(deduced_count), str(alarms), str(deduces)))

    def _check_rca(self, rca, expected_alarms, inspected):
        self.assertEqual(len(expected_alarms), len(rca['nodes']))
        for expected_alarm in expected_alarms:
            self.assertIsNotNone(
                g_utils.first_match(rca['nodes'], **expected_alarm),
                'expected_alarm is not in the rca %s' % str(expected_alarm))
        rca_inspected = rca['nodes'][rca['inspected_index']]
        self.assertTrue(g_utils.is_subset(inspected, rca_inspected),
                        'Invalid inspected item \n%s\n%s' %
                        (str(rca_inspected), str(inspected)))
