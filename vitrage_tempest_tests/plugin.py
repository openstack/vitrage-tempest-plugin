# Copyright 2015
# All Rights Reserved.
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


import os

# noinspection PyPackageRequirements
from tempest import config
# noinspection PyPackageRequirements
from tempest.test_discover import plugins

from vitrage_tempest_tests import config as config_rca_engine


class VitrageTempestPlugin(plugins.TempestPlugin):
    def load_tests(self):
        base_path = os.path.split(os.path.dirname(
            os.path.abspath(__file__)))[0]
        test_dir = "vitrage_tempest_tests/tests"
        full_test_dir = os.path.join(base_path, test_dir)
        return full_test_dir, base_path

    def register_opts(self, conf):
        config.register_opt_group(
            conf, config_rca_engine.service_available_group,
            config_rca_engine.ServiceAvailableGroup)
        config.register_opt_group(
            conf, config_rca_engine.rca_engine_group,
            config_rca_engine.RcaEngineGroup)

    def get_opt_lists(self):
        return [(config_rca_engine.rca_engine_group.name,
                 config_rca_engine.rca_engine_group)]
