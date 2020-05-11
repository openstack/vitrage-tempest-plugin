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

from oslo_log import log as logging
from oslo_serialization import jsonutils
from testtools import matchers

from vitrage_tempest_plugin.tests.base import BaseVitrageTempest
from vitrage_tempest_plugin.tests.base import IsEmpty
from vitrage_tempest_plugin.tests.base import IsNotEmpty
from vitrage_tempest_plugin.tests.common.constants import \
    CINDER_VOLUME_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import \
    NOVA_INSTANCE_DATASOURCE
from vitrage_tempest_plugin.tests.common.constants import VertexProperties as \
    VProps
from vitrage_tempest_plugin.tests.common import neutron_utils
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

    @classmethod
    def setUpClass(cls):
        super(TestResource, cls).setUpClass()
        cls.instances = nova_utils.create_instances(num_instances=1,
                                                    set_public_network=True)

    # noinspection PyPep8Naming
    @classmethod
    def tearDownClass(cls):
        super(TestResource, cls).tearDownClass()
        nova_utils.delete_created_instances(cls.instances)

    @utils.tempest_logger
    def test_compare_cli_vs_api_resource_list(self):
        """resource list """
        api_resources = self.vitrage_client.resource.list(
            all_tenants=True)

        LOG.info("api_resources = %s", api_resources)

        cli_resources = utils.run_vitrage_command(
            'vitrage resource list --all -f json')

        self._compare_resources(api_resources, cli_resources)

    @utils.tempest_logger
    def test_default_resource_list(self):
        """resource list with default query

        get the resources: network, instance, port, zone, host, cluster
        """
        # TODO(e0ne): split this test to verify that only network,
        # instance and port are returned to non-admin user.
        resources = self.vitrage_client.resource.list(all_tenants=False)
        has_shared_network = neutron_utils.get_shared_network()
        num_resources = 7 if has_shared_network else 6
        self.assertThat(resources, matchers.HasLength(num_resources))

    @utils.tempest_logger
    def test_resource_list_with_all_tenants(self):
        """resource list with all tenants

        get the resources:

        """
        instances = None
        try:
            resources_before = self.vitrage_client.resource.list(
                all_tenants=True)
            instances = nova_utils.create_instances(num_instances=1,
                                                    set_public_network=True)
            resources = self.vitrage_client.resource.list(all_tenants=True)

            self.assertEqual(len(resources_before) + 2, len(resources))

        finally:
            if instances:
                nova_utils.delete_created_instances(instances)

    @utils.tempest_logger
    def test_resource_list_with_existing_type(self):
        """resource list with existing type

        get the resource: one instance
        """
        resources = self.vitrage_client.resource.list(
            resource_type=NOVA_INSTANCE_DATASOURCE,
            all_tenants=True)
        self.assertThat(resources, matchers.HasLength(1))

    @utils.tempest_logger
    def test_resource_list_with_no_existing_type(self):
        """resource list with no existing type"""
        resources = self.vitrage_client.resource.list(
            resource_type=CINDER_VOLUME_DATASOURCE,
            all_tenants=True)
        self.assertThat(resources, IsEmpty())

    @utils.tempest_logger
    def test_resource_list_with_query_existing(self):
        resources = self.vitrage_client.resource.list(
            resource_type=NOVA_INSTANCE_DATASOURCE,
            all_tenants=True,
            query='{"==": {"name": "vm-0"}}'
        )
        self.assertThat(resources, matchers.HasLength(1))

    @utils.tempest_logger
    def test_resource_list_with_query_none_existing(self):
        resources = self.vitrage_client.resource.list(
            resource_type=NOVA_INSTANCE_DATASOURCE,
            all_tenants=True,
            query='{"==": {"name": "kuku-does-not-exist"}}'
        )
        self.assertThat(resources, matchers.HasLength(0))

    @utils.tempest_logger
    def test_resource_count(self):
        resources = self.vitrage_client.resource.count(
            resource_type=NOVA_INSTANCE_DATASOURCE,
            all_tenants=True,
            query='{"==": {"name": "vm-0"}}'
        )
        self.assertThat(resources, matchers.HasLength(1))
        self.assertEqual(1, resources[NOVA_INSTANCE_DATASOURCE])

    @utils.tempest_logger
    def test_resource_count_empty(self):
        resources = self.vitrage_client.resource.count(
            resource_type=NOVA_INSTANCE_DATASOURCE,
            all_tenants=True,
            query='{"==": {"name": "kuku-does-not-exist"}}'
        )
        self.assertThat(resources, matchers.HasLength(0))

    def test_resource_show_with_no_existing_resource(self):
        """resource_show test no existing resource"""
        try:

            self.assertRaises(ClientException,
                              self.vitrage_client.resource.get,
                              'test_for_no_existing')
        finally:
            nova_utils.delete_all_instances()

    def _compare_resources(self, api_resources, cli_resources):
        self.assertThat(api_resources, IsNotEmpty(),
                        'The resources taken from rest api is empty')
        self.assertThat(cli_resources, IsNotEmpty(),
                        'The resources taken from rest api is empty')

        sorted_cli_resources = sorted(
            jsonutils.loads(cli_resources),
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

            # Don't compare the state for Neutron ports. See bug #1776921
            if 'neutron.port' != cli_resource.get("Type").lower():
                self.assertEqual(
                    cli_resource.get("State").lower(),
                    api_resource.get(VProps.VITRAGE_OPERATIONAL_STATE).lower())
