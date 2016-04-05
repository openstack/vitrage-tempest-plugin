# Copyright 2016 Nokia
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
# import json

import vitrage_tempest_tests.tests.utils as utils

from oslo_log import log as logging

from vitrage.api.controllers.v1.alarms import AlarmsController
from vitrage_tempest_tests.tests.api.base import BaseVitrageTest

LOG = logging.getLogger(__name__)


class AlarmsHelper(BaseVitrageTest):
    """Alarms test class for Vitrage API tests."""

    def setUp(self):
        super(AlarmsHelper, self).setUp()

    @staticmethod
    def get_api_alarms():
        """Get Alarms returned by the v1 client """
        try:
            alarms = AlarmsController().get_alarms()
        except Exception as e:
            LOG.exception("Failed to get alarms %s ", e)
            return None
        return alarms

    def get_all_alarms(self):
        """Get Alarms returned by the cli """
        return utils.run_vitrage_command_with_user(
            'vitrage alarms list', self.conf.service_credentials.user)

    @staticmethod
    def filter_alarms(alarms_list, component):
        """Filter alarms by component """
        filtered_alarms_list = []
        LOG.debug("The component is " + component)
        for alarm in alarms_list:
            if component in alarm["id"]:
                filtered_alarms_list.add(alarm)
        return filtered_alarms_list

    """ CREATE ALARMS PER COMPONENT """
    def create_alarms_per_component(self, component):
        """Break something to create alarm for each component """

        LOG.debug("The component is " + component)
        switcher = {
            "nova": self._nova_alarms(),
            "nagios": self._nagios_alarms(),
            "aodh": self._aodh_alarm(),
        }

        """ Get the function from switcher dictionary """
        func = switcher.get(component, lambda: "nothing")
        """ Execute the function """
        return func()

    def _nova_alarms(self):
        flavor_id = self.get_flavor_id_from_list()
        image_id = self.get_image_id_from_list()

        self.create_vm_with_exist_image("alarm_vm", flavor_id, image_id)

    @staticmethod
    def _nagios_alarm():
        return "Not supported yet"

    @staticmethod
    def _aodh_alarm():
        return "Not supported yet"

    @staticmethod
    def compare_alarms_lists(api_alarms, cli_alarms):
        """Validate alarm existence """
        if not api_alarms:
            LOG.error("The alarms list taken from api is empty")
            return False
        if not cli_alarms:
            LOG.error("The alarms list taken from cli is empty")
            return False

            # parsed_alarms = json.loads(cli_alarms)
            # LOG.debug("The alarms list taken from cli is : " +
            #           json.dumps(parsed_alarms))
            # LOG.debug("The alarms list taken by api is : %s",
            #           json.dumps(api_alarms))
            #
            # cli_items = sorted(parsed_topology.items())
            # api_items = sorted(api_alarms.items())
            #
            # for item in cli_items[4][1]:
            #     item.pop(VProps.UPDATE_TIMESTAMP, None)
            #
            # for item in api_items[4][1]:
            #     item.pop(VProps.UPDATE_TIMESTAMP, None)
            #
            # return cli_items == api_items

    @staticmethod
    def validate_alarms_correctness(alarms, component):
        """Validate alarm existence """
        if not alarms:
            LOG.error("The alarms list is empty")
            return False
        LOG.debug("The component is " + component)
