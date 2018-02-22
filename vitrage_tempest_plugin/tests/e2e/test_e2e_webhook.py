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
import ast

from oslo_log import log as logging
import requests
from six.moves import BaseHTTPServer
import socket
from testtools import matchers
from threading import Thread
import time

from vitrage_tempest_plugin.tests.base import IsEmpty
from vitrage_tempest_plugin.tests.common.constants import VertexProperties as \
    VProps
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils

from vitrage_tempest_plugin.tests.e2e.test_actions_base import TestActionsBase
from vitrage_tempest_plugin.tests import utils


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
NOTIFICATION = 'notification'
PAYLOAD = 'payload'
MAIN_FILTER = {NOTIFICATION,
               PAYLOAD}
DOCTOR_ALARM_FILTER = {VProps.VITRAGE_ID,
                       VProps.RESOURCE,
                       VProps.NAME,
                       VProps.UPDATE_TIMESTAMP,
                       VProps.VITRAGE_TYPE,
                       VProps.VITRAGE_CATEGORY,
                       VProps.STATE,
                       VProps.VITRAGE_OPERATIONAL_SEVERITY}
RESOURCE_FILTER = {VProps.VITRAGE_ID,
                   VProps.ID,
                   VProps.NAME,
                   VProps.VITRAGE_CATEGORY,
                   VProps.UPDATE_TIMESTAMP,
                   VProps.VITRAGE_OPERATIONAL_STATE,
                   VProps.VITRAGE_TYPE}
messages = []


class TestWebhook(TestActionsBase):

    @classmethod
    def setUpClass(cls):
        super(TestWebhook, cls).setUpClass()
        cls._template = v_utils.add_template("e2e_webhooks.yaml")
        # Configure mock server.
        cls.mock_server_port = _get_free_port()
        cls.mock_server = MockHTTPServer(('localhost', cls.mock_server_port),
                                         MockServerRequestHandler)

        # Start running mock server in a separate thread.
        cls.mock_server_thread = Thread(target=cls.mock_server.serve_forever)
        cls.mock_server_thread.setDaemon(True)
        cls.mock_server_thread.start()
        cls.URL_PROPS = 'http://localhost:%s/' % cls.mock_server_port

    @classmethod
    def tearDownClass(cls):
        if cls._template is not None:
            v_utils.delete_template(cls._template['uuid'])

    def setUp(self):
        super(TestWebhook, self).setUp()

    def tearDown(self):
        super(TestWebhook, self).tearDown()
        del messages[:]
        self._delete_webhooks()
        self.mock_server.reset_requests_list()

    @utils.tempest_logger
    def test_basic_event(self):

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
            self.assertThat(self.mock_server.requests, matchers.HasLength(1),
                            'Wrong number of notifications for raise alarm')

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_1)

            # Check event undo received
            self.assertThat(self.mock_server.requests, matchers.HasLength(2),
                            'Wrong number of notifications for clear alarm')

        finally:
            self._trigger_undo_action(TRIGGER_ALARM_1)

    @utils.tempest_logger
    def test_with_no_filter(self):
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
            self.assertThat(self.mock_server.requests, matchers.HasLength(1),
                            'Wrong number of notifications for raise alarm')

            # Raise another alarm
            self._trigger_do_action(TRIGGER_ALARM_2)

            # Check second event received
            self.assertThat(self.mock_server.requests, matchers.HasLength(2),
                            'Wrong number of notifications for clear alarm')

        finally:
            self._trigger_undo_action(TRIGGER_ALARM_1)
            self._trigger_undo_action(TRIGGER_ALARM_2)

    @utils.tempest_logger
    def test_with_no_match(self):
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
            self.assertThat(self.mock_server.requests, IsEmpty(),
                            'event should not have passed filter')

            # Raise another alarm
            self._trigger_do_action(TRIGGER_ALARM_2)

            # Check second event not received
            self.assertThat(self.mock_server.requests, IsEmpty(),
                            'event should not have passed filter')

        finally:
            self._trigger_undo_action(TRIGGER_ALARM_1)
            self._trigger_undo_action(TRIGGER_ALARM_2)

    @utils.tempest_logger
    def test_multiple_webhooks(self):
        """Test to check filter by type and with no filter (with 2 separate

        webhooks)
        """

        try:

            # Add webhook
            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS,
                regex_filter=TYPE_FILTER,
            )

            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS
            )

            # Raise alarm
            self._trigger_do_action(TRIGGER_ALARM_1)

            # Check event received
            self.assertThat(self.mock_server.requests, matchers.HasLength(2),
                            'event not posted to all webhooks')

            # Raise another alarm
            self._trigger_do_action(TRIGGER_ALARM_2)

            # Check second event received
            self.assertThat(self.mock_server.requests, matchers.HasLength(4),
                            'event not posted to all webhooks')

        finally:
            self._trigger_undo_action(TRIGGER_ALARM_1)
            self._trigger_undo_action(TRIGGER_ALARM_2)

    @utils.tempest_logger
    def test_for_deduced_alarm(self):

        try:
            # Add webhook with filter for the deduced alarm
            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS,
                regex_filter=NAME_FILTER_FOR_DEDUCED,
                headers=HEADERS_PROPS
            )

            # Raise the trigger alarm
            self._trigger_do_action(TRIGGER_ALARM_WITH_DEDUCED)

            # Check event received - expected one for the deduced alarm
            # (the trigger alarm does not pass the filter). This test verifies
            # that the webhook is called only once for the deduced alarm.
            time.sleep(1)
            self.assertThat(self.mock_server.requests, matchers.HasLength(1),
                            'Wrong number of notifications for deduced alarm')

            # Undo
            self._trigger_undo_action(TRIGGER_ALARM_WITH_DEDUCED)

            # Check event undo received
            time.sleep(1)
            self.assertThat(self.mock_server.requests, matchers.HasLength(2),
                            'Wrong number of notifications '
                            'for clear deduced alarm')

        finally:
            self._trigger_undo_action(TRIGGER_ALARM_WITH_DEDUCED)

    @utils.tempest_logger
    def test_payload_format(self):

        try:

            TempestClients.vitrage().webhook.add(
                url=self.URL_PROPS,
                headers=HEADERS_PROPS
            )

            # Raise the trigger alarm
            self._trigger_do_action(TRIGGER_ALARM_1)

            # pre check that correct amount of notifications sent
            self.assertThat(self.mock_server.requests, matchers.HasLength(1),
                            'Wrong number of notifications for alarm')
            self.assertThat(messages, matchers.HasLength(1),
                            'Wrong number of messages for alarm')

            alarm = ast.literal_eval(messages[0])

            # check that only specified fields are sent for the alarm,
            # payload and resource
            passed_filter = utils.filter_data(alarm,
                                              MAIN_FILTER,
                                              match_filter=False)

            self.assertThat(passed_filter,
                            IsEmpty(),
                            "Wrong main fields sent")

            payload = alarm.get(PAYLOAD)
            if payload:
                passed_filter = utils.filter_data(payload,
                                                  DOCTOR_ALARM_FILTER,
                                                  match_filter=False)

                self.assertThat(passed_filter,
                                IsEmpty(),
                                "Wrong alarm fields sent")

                sent_fields = utils.filter_data(payload, DOCTOR_ALARM_FILTER)

                self.assertEqual(DOCTOR_ALARM_FILTER, sent_fields,
                                 "Some alarm fields not sent")

                resource = payload.get(VProps.RESOURCE)
                if resource:
                    passed_filter = utils.filter_data(resource,
                                                      RESOURCE_FILTER,
                                                      match_filter=False)

                    self.assertThat(passed_filter,
                                    IsEmpty(),
                                    "Wrong resource fields sent")

                    sent_fields = utils.filter_data(resource, RESOURCE_FILTER)

                    self.assertEqual(RESOURCE_FILTER, sent_fields,
                                     "Some resource fields not sent")
        finally:
            self._trigger_undo_action(TRIGGER_ALARM_1)

    @staticmethod
    def _delete_webhooks():
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

        content_len = int(self.headers.get('content-length', 0))
        # save received JSON
        messages.append(self.rfile.read(content_len).decode('utf-8'))
        # send fake response
        self.send_response(requests.codes.ok)
        self.end_headers()
        return

    def log_message(self, format, *args):
        pass
