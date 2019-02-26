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
from testtools import matchers

from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrageclient.exceptions import ClientException

LOG = logging.getLogger(__name__)

URL = 'url'
REGEX_FILTER = 'regex_filter'
HEADERS = 'headers'
HEADERS_PROPS = '{"content": "application/json"}'
REGEX_PROPS = '{"name": "e2e.*"}'


class TestWebhook(BaseVitrageTempest):
    """Webhook test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestWebhook, cls).setUpClass()
        cls.pre_test_webhook_count = \
            len(cls.vitrage_client.webhook.list())

    def test_add_webhook(self):

        webhooks = self.vitrage_client.webhook.list()
        self.assertThat(webhooks,
                        matchers.HasLength(self.pre_test_webhook_count),
                        'Amount of webhooks should be '
                        'the same as before the test')

        created_webhook = self.vitrage_client.webhook.add(
            url="https://www.test.com",
            regex_filter=REGEX_PROPS,
            headers=HEADERS_PROPS
        )

        self.assertIsNone(created_webhook.get('ERROR'), 'webhook not '
                                                        'created')
        self.assertEqual(created_webhook[HEADERS],
                         HEADERS_PROPS,
                         'headers not created correctly')
        self.assertEqual(created_webhook[REGEX_FILTER],
                         REGEX_PROPS,
                         'regex not created correctly')
        self.assertEqual(created_webhook[URL],
                         "https://www.test.com",
                         'URL not created correctly')

        webhooks = self.vitrage_client.webhook.list()

        self.assertThat(webhooks,
                        matchers.HasLength(self.pre_test_webhook_count + 1))
        self.vitrage_client.webhook.delete(
            created_webhook['id'])

    def test_delete_webhook(self):
        webhooks = self.vitrage_client.webhook.list()
        self.assertThat(webhooks,
                        matchers.HasLength(self.pre_test_webhook_count),
                        'Amount of webhooks should '
                        'be the same as before the test')

        created_webhook = self.vitrage_client.webhook.add(
            url="https://www.test.com",
            regex_filter=REGEX_PROPS,
            headers=HEADERS_PROPS
        )

        created_webhook = self.vitrage_client.webhook.delete(
            id=created_webhook['id'])
        self.assertIsNotNone(created_webhook.get('SUCCESS'),
                             'failed to delete')
        self.assertThat(webhooks,
                        matchers.HasLength(self.pre_test_webhook_count),
                        'No webhooks should exist after deletion')

    def test_delete_non_existing_webhook(self):
        self.assertRaises(ClientException,
                          self.vitrage_client.webhook.delete,
                          'non existent')

    def test_list_webhook(self):

        webhooks = self.vitrage_client.webhook.list()
        self.assertThat(webhooks,
                        matchers.HasLength(self.pre_test_webhook_count),
                        'Amount of webhooks should be '
                        'the same as before the test')

        created_webhook = self.vitrage_client.webhook.add(
            url="https://www.test.com",
            regex_filter=REGEX_PROPS,
            headers=HEADERS_PROPS
        )

        webhooks = self.vitrage_client.webhook.list()
        self.assertThat(webhooks,
                        matchers.HasLength(self.pre_test_webhook_count + 1))
        self.assertEqual(created_webhook[HEADERS], webhooks[0][HEADERS])
        self.assertEqual(created_webhook['id'], webhooks[0]['id'])
        self.assertEqual(created_webhook[REGEX_FILTER],
                         webhooks[0][REGEX_FILTER])

        self.vitrage_client.webhook.delete(created_webhook['id'])

    def test_show_webhook(self):
        webhooks = self.vitrage_client.webhook.list()
        self.assertThat(webhooks,
                        matchers.HasLength(self.pre_test_webhook_count),
                        'Amount of webhooks should be '
                        'the same as before the test')

        created_webhook = self.vitrage_client.webhook.add(
            url="https://www.test.com",
            regex_filter=REGEX_PROPS,
            headers=HEADERS_PROPS
        )

        show_webhook = self.vitrage_client.webhook.show(created_webhook['id'])

        self.assertIsNotNone(show_webhook, 'webhook not listed')
        self.assertEqual(created_webhook[HEADERS],
                         show_webhook[HEADERS],
                         'headers mismatch')
        self.assertEqual(created_webhook[REGEX_FILTER],
                         show_webhook[REGEX_FILTER],
                         'regex mismatch')
        self.assertEqual(created_webhook[URL],
                         show_webhook[URL],
                         'URL mismatch')

        self.vitrage_client.webhook.delete(created_webhook['id'])
