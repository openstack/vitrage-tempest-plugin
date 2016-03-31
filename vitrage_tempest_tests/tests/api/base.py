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
from oslo_log import log as logging
from oslotest import base
from vitrage_tempest_tests.tests.base_mock import BaseMock

import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)


class BaseVitrageTest(base.BaseTestCase):
    """Base test class for Vitrage API tests."""

    def __init__(self, *args, **kwds):
        super(BaseVitrageTest, self).__init__(*args, **kwds)
        self.mock_client = BaseMock()

    def _create_graph_by_mock(self):
        """Create MOCK Graph and copied to the string """
        processor = self.mock_client.create_processor_with_graph()
        entity_graph = processor.entity_graph
        mock_graph_output = entity_graph.output_graph()
        LOG.info("The mock graph is : " + mock_graph_output)

    @staticmethod
    def get_flavor_id_from_list():
        text_out = utils.run_vitrage_command("nova flavor-list")
        try:
            flavor_id = utils.get_regex_result("\|\s+(\d+)\s+\|",
                                               text_out.splitlines()[3])
        except Exception as e:
            LOG.exception("Failed to get flavor id from the list %s ", e)
            return None

        LOG.debug("The flavor id from the list is " + flavor_id)
        return flavor_id

    @staticmethod
    def get_image_id_from_list():
        text_out = utils.run_vitrage_command("glance image-list")
        try:
            image_id = utils.get_regex_result("\|\s+(.*)\s+\|",
                                              text_out.splitlines()[3])
            image_id = image_id.split(" ")[0]
        except Exception as e:
            LOG.exception("Failed to get image id from the list %s ", e)
            return None

        LOG.debug("The image id from the list is " + image_id)
        return image_id

    @staticmethod
    def get_instance_id_by_name(vm_name):
        text_out = utils.run_vitrage_command("nova list")
        for line in text_out.splitlines():
            if vm_name in line:
                vm_id = utils.get_regex_result("\|\s+(.*)\s+\|", line)
                vm_id = vm_id.split(" ")[0]
                LOG.debug("The instance id from the nova list is " + vm_id)
                return vm_id
        return None

    @staticmethod
    def get_volume_id_by_name(vol_name):
        text_out = utils.run_vitrage_command("cinder list")
        for line in text_out.splitlines():
            if vol_name in line:
                vol_id = utils.get_regex_result("\|\s+(.*)\s+\|", line)
                vol_id = vol_id.split(" ")[0]
                LOG.debug("The volume id from the cinder list is " + vol_id)
                return vol_id
        return None

    @staticmethod
    def create_vm_with_exist_image(vm_name, flavor_id, image_id):
        utils.run_vitrage_command("nova boot " + vm_name + " --flavor " +
                                  flavor_id + " --image " + image_id)

        text_out = utils.run_vitrage_command("nova list")
        if vm_name in text_out:
            LOG.debug("The expected vm exist in the nova list")
        else:
            LOG.error("The expected vm not exist in the nova list")

    @staticmethod
    def create_volume_with_exist_size(vol_name):
        utils.run_vitrage_command("cinder create --name " + vol_name + " 5")

        text_out = utils.run_vitrage_command("cinder list")
        if vol_name in text_out:
            LOG.debug("The expected volume exist in the cinder list")
        else:
            LOG.error("The expected volume not exist in the cinder list")

    def attach_volume(self, vm_name, vol_name):
        vm_id = self.get_instance_id_by_name(vm_name)
        vol_id = self.get_volume_id_by_name(vol_name)

        utils.run_vitrage_command("nova volume-attach " + vm_id + " " + vol_id)

        text_out = utils.run_vitrage_command("cinder list")
        if vm_id in text_out:
            LOG.debug("The expected volume attached to vm")
        else:
            LOG.error("The expected volume did not attached to vm")
