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

from oslo_log import log as logging

from vitrage_tempest_plugin.tests.e2e.test_basic_actions import TestActionsBase

LOG = logging.getLogger(__name__)


class BaseTestEvents(TestActionsBase):
    """Test class for Vitrage event API"""

    def _check_alarms(self):
        api_alarms = self.vitrage_client.alarm.list(vitrage_id='all',
                                                    all_tenants=True)
        if api_alarms:
            return True, api_alarms
        return False, api_alarms

    def _post_event(self, event_time, event_type, details):
        event_time_iso = event_time.isoformat()
        self.vitrage_client.event.post(event_time_iso, event_type, details)
