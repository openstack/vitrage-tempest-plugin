# Copyright 2017 Nokia
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

import datetime
import six
import unittest

from oslo_log import log as logging
from vitrage.common.constants import DatasourceProperties as DSProps
from vitrage.datasources import NEUTRON_PORT_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage import storage
from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrage_tempest_plugin.tests.common import nova_utils

LOG = logging.getLogger(__name__)


INSTANCE_NAME = 'test-persistor-vm'

INSTANCE_CREATE_EVENT = {
    DSProps.ENTITY_TYPE: NOVA_INSTANCE_DATASOURCE,
    DSProps.EVENT_TYPE: 'compute.instance.create.end',
    'hostname': INSTANCE_NAME + '-0'
}

PORT_CREATE_EVENT = {
    DSProps.ENTITY_TYPE: NEUTRON_PORT_DATASOURCE,
    DSProps.EVENT_TYPE: 'port.create.end',
}

PORT_UPDATE_EVENT = {
    DSProps.ENTITY_TYPE: NEUTRON_PORT_DATASOURCE,
    DSProps.EVENT_TYPE: 'port.update.end',
}


def get_first_match(events, event):
    for curr_event in events:
        if six.viewitems(event) <= six.viewitems(curr_event.payload):
            return curr_event


class TestEvents(BaseVitrageTempest):
    """Test class for Vitrage persisror service"""

    def setUp(self):
        super(TestEvents, self).setUp()

    def tearDown(self):
        super(TestEvents, self).tearDown()

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        super(TestEvents, cls).setUpClass()
        cls.db_connection = storage.get_connection_from_config(cls.conf)

    @unittest.skip("persistency is disabled in queens")
    def test_create_instance(self):
        """This function validates creating instance events.

        Create instance generates three ordered events.
        1. neutron port is created.
        2. the port is updated to the created instance.
        3. nova instance is created with the given hostname.
        """
        try:

            # Action
            time_before_action = datetime.datetime.utcnow()
            nova_utils.create_instances(num_instances=1,
                                        name=INSTANCE_NAME,
                                        set_public_network=True)

            writen_events = self._load_db_events(time_before_action)

            port_create_event = get_first_match(writen_events,
                                                PORT_CREATE_EVENT)

            self.assertIsNotNone(port_create_event,
                                 "port.create.end event is not writen to db")

            port_update_event = get_first_match(writen_events,
                                                PORT_UPDATE_EVENT)

            self.assertIsNotNone(port_update_event,
                                 "port.update.end event is not writen to db")

            instance_create_event = get_first_match(writen_events,
                                                    INSTANCE_CREATE_EVENT)

            self.assertIsNotNone(instance_create_event,
                                 "compute.instance.create.end event is not "
                                 "writen to db")

            # Check correct timestamp order
            events_timestamp_list = \
                [port_create_event.collector_timestamp,
                 port_update_event.collector_timestamp,
                 instance_create_event.collector_timestamp]

            self.assertEqual(sorted(events_timestamp_list),
                             events_timestamp_list,
                             "Events Timestamp order is wrong")

            # Check correct event_id order
            events_id_list = \
                [port_create_event.event_id,
                 port_update_event.event_id,
                 instance_create_event.event_id]

            self.assertEqual(sorted(events_id_list),
                             events_id_list,
                             "Events id order is wrong")

        except Exception as e:
            self._handle_exception(e)
            raise

        finally:
            nova_utils.delete_all_instances()

    def _load_db_events(self, time_before_action):
        writen_events = self.db_connection.events.query(
            gt_collector_timestamp=time_before_action)

        return writen_events
