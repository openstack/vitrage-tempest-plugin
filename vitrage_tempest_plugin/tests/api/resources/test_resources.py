# Copyright 2017 ZTE, Nokia
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

import json

from oslo_log import log as logging

import unittest

from vitrage.common.constants import VertexProperties as VProps
from vitrage.datasources import CINDER_VOLUME_DATASOURCE
from vitrage.datasources import NOVA_INSTANCE_DATASOURCE
from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrage_tempest_plugin.tests.common import nova_utils
from vitrage_tempest_plugin.tests import utils
from vitrageclient.exceptions import ClientException

LOG = logging.getLogger(__name__)


class TestResource(BaseVitrageTempest):
    """Test class for Vitrage resource API tests."""

    properties = (VProps.VITRAGE_ID,
                  VProps.VITRAGE_TYPE,
                  VProps.ID,
                  VProps.STATE,
                  VProps.VITRAGE_AGGREGATED_STATE)

    def setUp(self):
        super(TestResource, self).setUp()

    def tearDown(self):
        super(TestResource, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestResource, cls).setUpClass()

    @utils.tempest_logger
    def test_compare_cli_vs_api_resource_list(self):
        """resource list """
        try:
            instances = nova_utils.create_instances(num_instances=1,
                                                    set_public_network=True)
            self.assertNotEqual(len(instances), 0,
                                'The instances list is empty')
            api_resources = self.vitrage_client.resource.list(
                all_tenants=True)

            LOG.info("api_resources = %s", api_resources)

            cli_resources = utils.run_vitrage_command(
                'vitrage resource list --all -f json', self.conf)

            self._compare_resources(api_resources, cli_resources)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            nova_utils.delete_all_instances()

    @utils.tempest_logger
    def test_default_resource_list(self):
        """resource list with default query

        get the resources: network, instance, port
        """
        try:
            instances = nova_utils.create_instances(num_instances=1,
                                                    set_public_network=True)
            self.assertNotEqual(len(instances), 0,
                                'The instances list is empty')
            resources = self.vitrage_client.resource.list(all_tenants=False)
            self.assertEqual(3, len(resources))
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            nova_utils.delete_all_instances()

    @utils.tempest_logger
    def test_resource_list_with_all_tenants(self):
        """resource list with all tenants

        get the resources:

        """
        try:
            resources_before = self.vitrage_client.resource.list(
                all_tenants=True)
            instances = nova_utils.create_instances(num_instances=1,
                                                    set_public_network=True)
            self.assertNotEqual(len(instances), 0,
                                'The instances list is empty')
            resources = self.vitrage_client.resource.list(all_tenants=True)

            self.assertEqual(len(resources_before) + 2, len(resources))
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            nova_utils.delete_all_instances()

    @utils.tempest_logger
    def test_resource_list_with_existing_type(self):
        """resource list with existing type

        get the resource: one instance
        """
        try:
            instances = nova_utils.create_instances(num_instances=1,
                                                    set_public_network=True)
            self.assertNotEqual(len(instances), 0,
                                'The instances list is empty')
            resources = self.vitrage_client.resource.list(
                resource_type=NOVA_INSTANCE_DATASOURCE,
                all_tenants=True)
            self.assertEqual(1, len(resources))
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            nova_utils.delete_all_instances()

    @utils.tempest_logger
    def test_resource_list_with_no_existing_type(self):
        """resource list with no existing type"""
        try:
            instances = nova_utils.create_instances(num_instances=1,
                                                    set_public_network=True)
            self.assertNotEqual(len(instances), 0,
                                'The instances list is empty')
            resources = self.vitrage_client.resource.list(
                resource_type=CINDER_VOLUME_DATASOURCE,
                all_tenants=True)
            self.assertEqual(0, len(resources))
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            nova_utils.delete_all_instances()

    @unittest.skip("CLI tests are ineffective and not maintained")
    def test_compare_resource_show(self):
        """resource_show test"""
        resource_list = self.vitrage_client.resource.list(all_tenants=False)
        self.assertNotEqual(len(resource_list), 0)
        for resource in resource_list:
            api_resource_show = \
                self.vitrage_client.resource.get(resource[VProps.VITRAGE_ID])
            cli_resource_show = utils.run_vitrage_command(
                'vitrage resource show ' + resource[VProps.VITRAGE_ID],
                self.conf)

            self._compare_resource_show(
                api_resource_show, cli_resource_show)

    def test_resource_show_with_no_existing_resource(self):
        """resource_show test no existing resource"""
        try:

            self.assertRaises(ClientException,
                              self.vitrage_client.resource.get(
                                  'test_for_no_existing'))
        except Exception as e:
            self._handle_exception(e)

        finally:
            nova_utils.delete_all_instances()

    def _compare_resources(self, api_resources, cli_resources):
        self.assertNotEqual(len(api_resources), 0,
                            'The resources taken from rest api is empty')
        self.assertNotEqual(len(cli_resources), 0,
                            'The resources taken from terminal is empty')

        sorted_cli_resources = sorted(
            json.loads(cli_resources),
            key=lambda resource: resource["ID"])
        sorted_api_resources = sorted(
            api_resources,
            key=lambda resource: resource["vitrage_id"])

        self.assertEqual(len(sorted_cli_resources),
                         len(sorted_api_resources), 'cli = %s --> api = %s' %
                         (sorted_cli_resources, sorted_api_resources))

        for cli_resource, api_resource in \
                zip(sorted_cli_resources, sorted_api_resources):

            self.assertEqual(
                cli_resource.get("ID").lower(),
                api_resource.get(VProps.VITRAGE_ID).lower())
            self.assertEqual(
                cli_resource.get("Type").lower(),
                api_resource.get(VProps.VITRAGE_TYPE).lower())
            self.assertEqual(
                cli_resource.get("Data Source ID").lower(),
                api_resource.get(VProps.ID).lower())
            self.assertEqual(
                cli_resource.get("State").lower(),
                api_resource.get(VProps.VITRAGE_OPERATIONAL_STATE).lower())

    def _compare_resource_show(self, api_resource_show,
                               cli_resource_show):
        self.assertIsNotNone(api_resource_show,
                             'The resource show taken from rest api is empty')
        self.assertIsNotNone(cli_resource_show,
                             'The resource show taken from terminal is empty')

        for item in self.properties:
            self.assertEqual(api_resource_show.get(item),
                             cli_resource_show.get(item))
