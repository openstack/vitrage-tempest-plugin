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

from oslo_config import cfg
from oslo_log import log as logging
from oslotest import base

import vitrage_tempest_tests.tests.utils as utils

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
logging.register_options(CONF)
logging.setup(CONF, "vitrage")
logging.set_defaults(default_log_levels=utils.extra_log_level_defaults)


class RunVitrageEnv(base.BaseTestCase):
    """RunVitrageEnv class. Run Vitrage env."""

    def __init__(self, *args, **kwds):
        super(RunVitrageEnv, self).__init__(*args, **kwds)

    def test_run_env(self):
        if self._show_vitrage_processes() is True:
            LOG.debug('The vitrage processed existed and should be removed')
            self._stop_vitrage_processes()

        self._get_env_params()

        utils.change_terminal_dir('/home/stack/devstack')
        utils.run_vitrage_command(". openrc " + self.user + " " +
                                  self.user)
        utils.run_from_terminal("openstack service create rca" +
                                " --name vitrage")
        utils.run_from_terminal("openstack endpoint create rca" +
                                # " --os-username " + self.user +
                                # " --os-username " + self.user +
                                # " --os-password " + self.password +
                                # " --os-auth-url " + self.url +
                                # " --os-project-name admin" +
                                " --adminurl http://" + self.host +
                                ":" + str(self.port) +
                                " --internalurl http://" + self.host +
                                ":" + str(self.port) +
                                " --publicurl http://" + self.host +
                                ":" + str(self.port) +
                                " --region RegionOne")

        utils.run_from_terminal("nohup vitrage-graph > /tmp/nohup-graph.out &")
        utils.run_from_terminal("nohup vitrage-api > /tmp/nohup-api.out &")

        if self._show_vitrage_processes() is False:
            LOG.error("No vitrage processes founded")
            raise ValueError("No vitrage processes founded")
        else:
            LOG.info('The vitrage processes exists')

        if self._validate_vitrage_processes() is False:
            LOG.error("The vitrage processes are not correct")
            self._stop_vitrage_processes()
            raise ValueError("The vitrage processes are not correct")

    @staticmethod
    def _show_vitrage_processes():
        text_out = utils.get_from_terminal(
            "ps -ef | grep vitrage-api | grep -v grep")
        text_out2 = utils.get_from_terminal(
            "ps -ef | grep vitrage-graph | grep -v grep")

        if ("vitrage-api" in text_out) and ("vitrage-graph" in text_out2):
            LOG.debug('The vitrage processes exists')
            return True
        elif "vitrage-api" in text_out:
            LOG.debug('Only vitrage-api process exist')
            return True
        elif "vitrage-graph" in text_out2:
            LOG.debug('Only vitrage-graph process exist')
            return True
        else:
            LOG.debug('The vitrage process does not run')
            return False

    def _get_env_params(self):
        conf = utils.get_conf()
        self.port = conf.api.port
        self.user = conf.service_credentials.user
        self.password = conf.service_credentials.password
        self.url = conf.service_credentials.auth_url + "/v2.0"
        self.host = utils.get_regex_result(
            "(\d+\.\d+\.\d+\.\d+)", self.url)
        self.identity_uri = conf.keystone_authtoken.identity_uri

    @staticmethod
    def _stop_vitrage_processes():
        text_out = utils.get_from_terminal("pgrep vitrage-api")
        if text_out != '':
            LOG.debug("The vitrage-api process exist")
            utils.run_from_terminal("kill -9 " + text_out)

        text_out2 = utils.get_from_terminal("pgrep vitrage-graph")
        if text_out2 != '':
            LOG.debug("The vitrage-graph process exist")
            utils.run_from_terminal("kill -9 " + text_out2)

    @staticmethod
    def _validate_vitrage_processes():
        errors_out = utils.get_from_terminal(
            "grep ERROR /tmp/nohup-graph.out | " +
            "grep ERROR /tmp/nohup-api.out | grep -v \'ERROR %\'")
        if errors_out != '':
            LOG.error("The errors are : " + errors_out)
            return False
        return True
