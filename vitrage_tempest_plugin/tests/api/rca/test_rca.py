# Copyright 2016 - Nokia
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

from vitrage.common.constants import VertexProperties as VProps
from vitrage_tempest_plugin.tests.api.rca.base import BaseRcaTest
from vitrage_tempest_plugin.tests.api.rca.base import RCA_ALARM_NAME
from vitrage_tempest_plugin.tests.common import nova_utils
from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils
from vitrage_tempest_plugin.tests import utils

import unittest

LOG = logging.getLogger(__name__)


class TestRca(BaseRcaTest):
    """RCA test class for Vitrage API tests."""

    def setUp(self):
        super(TestRca, self).setUp()

    def tearDown(self):
        super(TestRca, self).tearDown()

    @classmethod
    def setUpClass(cls):
        super(TestRca, cls).setUpClass()
        cls._template = v_utils.add_template('host_aodh_alarm_for_rca.yaml')

    @classmethod
    def tearDownClass(cls):
        if cls._template is not None:
            v_utils.delete_template(cls._template['uuid'])

    @unittest.skip("CLI tests are ineffective and not maintained")
    @utils.tempest_logger
    def test_compare_cli_and_api(self):
        """compare_cli_and_api test

        There test validate correctness of rca of created
        aodh event alarms, and equals them with cli rca
        """
        try:
            instances = nova_utils.create_instances(num_instances=1,
                                                    set_public_network=True)
            self.assertNotEqual(len(instances), 0, 'Failed to create instance')

            instance_alarm = self._create_alarm(
                resource_id=instances[0].id,
                alarm_name='instance_rca_alarm', unic=True)

            vitrage_id = instance_alarm.get(VProps.VITRAGE_ID)
            api_rca = self.vitrage_client.rca.get(alarm_id=vitrage_id)
            cli_rca = utils.run_vitrage_command(
                'vitrage rca show ' + vitrage_id, self.conf)

            self._compare_rca(api_rca, cli_rca)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._clean_all()

    @unittest.skip("skipping test - test not working")
    @utils.tempest_logger
    # TODO(nivo): check why creation of alarm doesnt return the alarm
    def test_validate_rca(self):
        """validate_rca test

        There tests validates correctness of rca of created aodh
        event alarm and correctness of relationship between host alarm
        to instance alarms (created by special template file),
        source alarm - aodh alarm on host
        target alarms - 2 instance alarms (caused 2 created instance)
        """
        try:
            nova_utils.create_instances(num_instances=2,
                                        set_public_network=True)
            host_alarm = self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            api_rca = self.vitrage_client.rca.get(
                alarm_id=host_alarm.get(VProps.VITRAGE_ID), all_tenants=True)

            self._validate_rca(rca=api_rca['nodes'])
            self._validate_relationship(links=api_rca['links'],
                                        alarms=api_rca['nodes'])
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._clean_all()

    @utils.tempest_logger
    def test_validate_deduce_alarms(self):
        """validate_deduce_alarms test

        There tests validates correctness of deduce alarms
        (created by special template file), and equals there
        resource_id with created instances id
        """
        try:
            instances = nova_utils.create_instances(num_instances=2,
                                                    set_public_network=True)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            api_alarms = self.vitrage_client.alarm.list(vitrage_id='all',
                                                        all_tenants=True)

            self._validate_deduce_alarms(alarms=api_alarms,
                                         instances=instances)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._clean_all()

    @utils.tempest_logger
    def test_validate_set_state(self):
        """validate_set_state test

        There tests validates correctness of topology resource
        state, after alarms creation (by special template file),
        source state - ERROR
        target state - SUBOPTIMAL (caused 2 created instance)
        """
        try:
            instances = nova_utils.create_instances(num_instances=2,
                                                    set_public_network=True)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            topology = self.vitrage_client.topology.get(all_tenants=True)

            self._validate_set_state(topology=topology['nodes'],
                                     instances=instances)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._clean_all()

    @unittest.skip("aodh notifier is not supported")
    @utils.tempest_logger
    def test_validate_notifier(self):
        """validate_notifier test

        There tests validates work of aodh alarm notifier -
        all created vitrage alarms appears in ceilometer
        alarms-list.
        IMPORTANT: enable notifiers=aodh in vitrage.conf file
        """
        try:
            nova_utils.create_instances(num_instances=2,
                                        set_public_network=True)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            vitrage_alarms = TempestClients.vitrage().alarm.list(
                vitrage_id='all', all_tenants=True)
            aodh_alarms = TempestClients.aodh().alarm.list()

            self._validate_notifier(alarms=aodh_alarms,
                                    vitrage_alarms=vitrage_alarms)
        except Exception as e:
            self._handle_exception(e)
            raise
        finally:
            self._clean_all()
