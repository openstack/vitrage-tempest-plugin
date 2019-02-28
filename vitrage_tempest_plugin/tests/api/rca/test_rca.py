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

from vitrage_tempest_plugin.tests.api.rca.base import BaseRcaTest
from vitrage_tempest_plugin.tests.api.rca.base import RCA_ALARM_NAME
from vitrage_tempest_plugin.tests.common import nova_utils
from vitrage_tempest_plugin.tests.common import vitrage_utils as v_utils
from vitrage_tempest_plugin.tests import utils

LOG = logging.getLogger(__name__)


class TestRca(BaseRcaTest):
    """RCA test class for Vitrage API tests."""

    def tearDown(self):
        super(TestRca, self).tearDown()
        self._clean_all()

    @classmethod
    def setUpClass(cls):
        super(TestRca, cls).setUpClass()
        cls._template = v_utils.add_template('host_aodh_alarm_for_rca.yaml')

    # noinspection PyPep8Naming
    @classmethod
    def tearDownClass(cls):
        super(TestRca, cls).tearDownClass()
        if cls._template is not None:
            v_utils.delete_template(cls._template['uuid'])

    @utils.tempest_logger
    def test_validate_deduce_alarms(self):
        """validate_deduce_alarms test

        There tests validates correctness of deduce alarms
        (created by special template file), and equals there
        resource_id with created instances id
        """
        instances = nova_utils.create_instances(num_instances=2,
                                                set_public_network=True)
        self._create_alarm(
            resource_id=self._get_hostname(),
            alarm_name=RCA_ALARM_NAME)
        api_alarms = self.vitrage_client.alarm.list(vitrage_id='all',
                                                    all_tenants=True)

        self._validate_deduce_alarms(alarms=api_alarms,
                                     instances=instances)

    @utils.tempest_logger
    def test_validate_set_state(self):
        """validate_set_state test

        There tests validates correctness of topology resource
        state, after alarms creation (by special template file),
        source state - ERROR
        target state - SUBOPTIMAL (caused 2 created instance)
        """
        instances = nova_utils.create_instances(num_instances=2,
                                                set_public_network=True)
        self._create_alarm(
            resource_id=self._get_hostname(),
            alarm_name=RCA_ALARM_NAME)
        topology = self.vitrage_client.topology.get(all_tenants=True)

        self._validate_set_state(topology=topology['nodes'],
                                 instances=instances)
