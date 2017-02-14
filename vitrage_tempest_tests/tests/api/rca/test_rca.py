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

import traceback

from oslo_log import log as logging

from vitrage.common.constants import VertexProperties as VProps
from vitrage_tempest_tests.tests.api.rca.base import BaseRcaTest
from vitrage_tempest_tests.tests.api.rca.base import RCA_ALARM_NAME
import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)


class TestRca(BaseRcaTest):
    """RCA test class for Vitrage API tests."""

    @classmethod
    def setUpClass(cls):
        super(TestRca, cls).setUpClass()

    @utils.tempest_logger
    def test_compare_cil_and_api(self):
        """compare_cil_and_api test

        There test validate correctness of rca of created
        aodh event alarms, and compare them with cli rca
        """
        try:
            instances = self._create_instances(num_instances=1)
            self.assertNotEqual(len(instances), 0, 'Failed to create instance')

            instance_alarm = self._create_alarm(
                resource_id=instances[0].id,
                alarm_name='instance_rca_alarm', unic=True)

            vitrage_id = self._get_value(
                instance_alarm, VProps.VITRAGE_ID)
            api_rca = self.vitrage_client.rca.get(alarm_id=vitrage_id)
            cli_rca = utils.run_vitrage_command(
                'vitrage rca show ' + vitrage_id, self.conf)

            self._compare_rca(api_rca, cli_rca)
        except Exception as e:
            traceback.print_exc()
            LOG.exception(e)
            raise
        finally:
            self._clean_all()

    @utils.tempest_logger
    def test_validate_rca(self):
        """validate_rca test

        There tests validates correctness of rca of created aodh
        event alarm and correctness of relationship between host alarm
        to instance alarms (created by special template file),
        source alarm - aodh alarm on host
        target alarms - 2 instance alarms (caused 2 created instance)
        """
        try:
            self._create_instances(num_instances=2)
            host_alarm = self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME,
                unic=False)
            api_rca = self.vitrage_client.rca.get(
                alarm_id=self._get_value(host_alarm,
                                         VProps.VITRAGE_ID))

            self._validate_rca(rca=api_rca['nodes'])
            self._validate_relationship(links=api_rca['links'],
                                        alarms=api_rca['nodes'])
        except Exception as e:
            traceback.print_exc()
            LOG.exception(e)
            raise
        finally:
            self._clean_all()

    @utils.tempest_logger
    def test_validate_deduce_alarms(self):
        """validate_deduce_alarms test

        There tests validates correctness of deduce alarms
        (created by special template file), and compare there
        resource_id with created instances id
        """
        try:
            instances = self._create_instances(num_instances=2)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            api_alarms = self.vitrage_client.alarm.list(vitrage_id=None)

            self._validate_deduce_alarms(alarms=api_alarms,
                                         instances=instances)
        except Exception as e:
            traceback.print_exc()
            LOG.exception(e)
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
            instances = self._create_instances(num_instances=2)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            topology = self.vitrage_client.topology.get(all_tenants=1)

            self._validate_set_state(topology=topology['nodes'],
                                     instances=instances)
        except Exception as e:
            traceback.print_exc()
            LOG.exception(e)
            raise
        finally:
            self._clean_all()

    @utils.tempest_logger
    def test_validate_notifier(self):
        """validate_notifier test

        There tests validates work of aodh alarm notifier -
        all created vitrage alarms appears in ceilometer
        alarms-list.
        IMPORTANT: enable notifiers=aodh in vitrage.conf file
        """
        try:
            self._create_instances(num_instances=2)
            self._create_alarm(
                resource_id=self._get_hostname(),
                alarm_name=RCA_ALARM_NAME)
            vitrage_alarms = self.vitrage_client.alarm.list(vitrage_id=None)
            ceilometer_alarms = self.ceilometer_client.alarms.list()

            self._validate_notifier(alarms=ceilometer_alarms,
                                    vitrage_alarms=vitrage_alarms)
        except Exception as e:
            traceback.print_exc()
            LOG.exception(e)
            raise
        finally:
            self._clean_all()
