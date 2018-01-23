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
import requests
from six.moves import BaseHTTPServer
import socket
from threading import Thread

from vitrage.common.constants import VertexProperties as VProps
from vitrage_tempest_tests.tests.common.tempest_clients import TempestClients
from vitrage_tempest_tests.tests.e2e.test_actions_base import TestActionsBase
from vitrage_tempest_tests.tests import utils

LOG = logging.getLogger(__name__)

TRIGGER_ALARM_1 = 'e2e.test_webhook.alarm1'
TRIGGER_ALARM_2 = 'e2e.test_webhook.alarm2'
TRIGGER_ALARM_WITH_DEDUCED = 'e2e.test_webhook.alarm_with_deduced'
URL = 'url'
REGEX_FILTER = 'regex_filter'
HEADERS = 'headers'
HEADERS_PROPS = '{"content": "application/json"}'
NAME_FILTER = '{"name": "e2e.*"}'
NAME_FILTER_FOR_DEDUCED = '{"name": "e2e.test_webhook.deduced"}'
TYPE_FILTER = '{"vitrage_type": "doctor"}'
FILTER_NO_MATCH = '{"name": "NO MATCH"}'


class TestWebhook(TestActionsBase):

    @classmethod
    def setUpClass(cls):
        super(TestWebhook, cls).setUpClass()
        # Configure mock server.
        cls.mock_server_port = _get_free_port()
        cls.mock_server = MockHTTPServer(('localhost', cls.mock_server_port),
                                         MockServerRequestHandler)

        # Start running mock server in a separate thread.
        cls.mock_server_thread = Thread(target=cls.mock_server.serve_forever)
        cls.mock_server_thread.setDaemon(True)
        cls.mock_server_thread.start()
        cls.URL_PROPS = 'http://localhost:%s/' % cls.mock_server_port

    @utils.tempest_logger
    def test_webhook_basic_event(self):

        try:

            # Add webhook with filter matching alarm
            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS,
                regex_filter=NAME_FILTER,
                headers=HEADERS_PROPS
            )

            # Raise alarm
            self._trigger_do_action(TRIGGER_ALARM_1)

            # Check event received
            self.assertEqual(1, len(self.mock_server.requests),
                             'Wrong number of notifications for raise alarm')

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_1)

            # Check event undo received
            self.assertEqual(2, len(self.mock_server.requests),
                             'Wrong number of notifications for clear alarm')

        finally:
            self._delete_webhooks()
            self._trigger_undo_action(TRIGGER_ALARM_1)
            self.mock_server.reset_requests_list()

    def test_webhook_with_no_filter(self):
        """Test to see that a webhook with no filter receives all

        notifications
        """

        try:

            # Add webhook
            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS,
                regex_filter=NAME_FILTER,
            )

            # Raise alarm
            self._trigger_do_action(TRIGGER_ALARM_1)

            # Check event received
            self.assertEqual(1, len(self.mock_server.requests),
                             'Wrong number of notifications for raise alarm')

            # Raise another alarm
            self._trigger_do_action(TRIGGER_ALARM_2)

            # Check second event received
            self.assertEqual(2, len(self.mock_server.requests),
                             'Wrong number of notifications for clear alarm')

        finally:
            self._delete_webhooks()
            self._trigger_undo_action(TRIGGER_ALARM_1)
            self._trigger_undo_action(TRIGGER_ALARM_2)
            self.mock_server.reset_requests_list()

    def test_webhook_with_no_match(self):
        """Test to check that filters with no match do not send event """

        try:

            # Add webhook
            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS,
                regex_filter=FILTER_NO_MATCH,
            )

            # Raise alarm
            self._trigger_do_action(TRIGGER_ALARM_1)

            # Check event not received
            self.assertEqual(0, len(self.mock_server.requests),
                             'event should not have passed filter')

            # Raise another alarm
            self._trigger_do_action(TRIGGER_ALARM_2)

            # Check second event not received
            self.assertEqual(0, len(self.mock_server.requests),
                             'event should not have passed filter')

        finally:
            self._delete_webhooks()
            self._trigger_undo_action(TRIGGER_ALARM_1)
            self._trigger_undo_action(TRIGGER_ALARM_2)
            self.mock_server.reset_requests_list()

    def test_multiple_webhooks(self):
        """Test to check filter by type and by ID (with 2 different

        webhooks)
        """

        host_id = self.orig_host[VProps.VITRAGE_ID]
        ID_FILTER = '{"%s": "%s"}' % (VProps.VITRAGE_RESOURCE_ID, host_id)

        try:

            # Add webhook
            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS,
                regex_filter=TYPE_FILTER,
            )

            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS,
                regex_filter=ID_FILTER,
            )

            # Raise alarm
            self._trigger_do_action(TRIGGER_ALARM_1)

            # Check event received
            self.assertEqual(2, len(self.mock_server.requests),
                             'event not posted to all webhooks')

            # Raise another alarm
            self._trigger_do_action(TRIGGER_ALARM_2)

            # Check second event received
            self.assertEqual(4, len(self.mock_server.requests),
                             'event not posted to all webhooks')

        finally:
            self._delete_webhooks()
            self._trigger_undo_action(TRIGGER_ALARM_1)
            self._trigger_undo_action(TRIGGER_ALARM_2)
            self.mock_server.reset_requests_list()

    # Will be un-commented-out in the next change
    #
    # @utils.tempest_logger
    # def test_webhook_for_deduced_alarm(self):
    #
    #     try:
    #
    #         # Add webhook with filter for the deduced alarm
    #         TempestClients.vitrage().webhook.add(
    #             url=self.URL_PROPS,
    #             regex_filter=NAME_FILTER_FOR_DEDUCED,
    #             headers=HEADERS_PROPS
    #         )
    #
    #         # Raise the trigger alarm
    #         self._trigger_do_action(TRIGGER_ALARM_WITH_DEDUCED)
    #
    #         # Check event received - expected one for the deduced alarm
    #       # (the trigger alarm does not pass the filter). This test verifies
    #         # that the webhook is called only once for the deduced alarm.
    #         self.assertEqual(1, len(self.mock_server.requests),
    #                        'Wrong number of notifications for deduced alarm')
    #
    #         # Undo
    #         self._trigger_undo_action(TRIGGER_ALARM_WITH_DEDUCED)
    #
    #         # Check event undo received
    #         self.assertEqual(2, len(self.mock_server.requests),
    #                        'Wrong number of notifications for clear deduced '
    #                          'alarm')
    #
    #     finally:
    #         self._delete_webhooks()
    #         self._trigger_undo_action(TRIGGER_ALARM_WITH_DEDUCED)
    #         self.mock_server.reset_requests_list()

    def _delete_webhooks(self):
        webhooks = TempestClients.vitrage().webhook.list()
        for webhook in webhooks:
            TempestClients.vitrage().webhook.delete(webhook['id'])


def _get_free_port():
    s = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    address, port = s.getsockname()
    s.close()
    return port


class MockHTTPServer(BaseHTTPServer.HTTPServer):

    def __init__(self, server, handler):
        BaseHTTPServer.HTTPServer.__init__(self, server, handler)
        self.requests = []

    def process_request(self, request, client_address):
        self.requests.append(request)
        LOG.info('received request: %s', str(request))
        BaseHTTPServer.HTTPServer.process_request(
            self, client_address=client_address, request=request)

    def reset_requests_list(self):
        self.requests = []


class MockServerRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_POST(self):

        # Process a HTTP Post request and return status code 200
        self.send_response(requests.codes.ok)
        self.end_headers()
        return
