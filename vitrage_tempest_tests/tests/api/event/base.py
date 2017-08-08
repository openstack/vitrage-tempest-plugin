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

from datetime import datetime
from oslo_log import log as logging

from vitrage import keystone_client
from vitrage import service
from vitrage_tempest_tests.tests.api.base import BaseApiTest
from vitrageclient import client as v_client


LOG = logging.getLogger(__name__)
DOWN = 'down'
UP = 'up'


class BaseTestEvents(BaseApiTest):
    """Test class for Vitrage event API"""

    # noinspection PyPep8Naming
    @classmethod
    def setUpClass(cls):
        cls.conf = service.prepare_service([])
        cls.vitrage_client = \
            v_client.Client('1', session=keystone_client.get_session(cls.conf))

    def _check_alarms(self):
        api_alarms = self.vitrage_client.alarm.list(vitrage_id='all',
                                                    all_tenants=True)
        if api_alarms:
            return True, api_alarms
        return False, api_alarms

    def _post_event(self, details):
        event_time = datetime.now()
        event_time_iso = event_time.isoformat()
        event_type = 'compute.host.down'
        self.vitrage_client.event.post(event_time_iso, event_type, details)

    @staticmethod
    def _create_doctor_event_details(hostname, status):
        return {
            'hostname': hostname,
            'source': 'sample_monitor',
            'cause': 'another alarm',
            'severity': 'critical',
            'status': status,
            'monitor_id': 'sample monitor',
            'monitor_event_id': '456',
        }
