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

import vitrage_tempest_tests.tests.utils as utils

import testtools

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
logging.register_options(CONF)
logging.setup(CONF, "vitrage")
logging.set_defaults(default_log_levels=utils.extra_log_level_defaults)


class StopVitrageEnv(testtools.TestCase):
    """StopVitrageEnv class. Stop Vitrage env."""

    def __init__(self, *args, **kwds):
        super(StopVitrageEnv, self).__init__(*args, **kwds)

    @staticmethod
    def test_stop_vitrage_processes():
        LOG.debug("Stop vitrage processes")
        text_out = utils.get_from_terminal("pgrep vitrage-api")
        if text_out != '':
            utils.run_from_terminal("kill -9 " + text_out)

        text_out2 = utils.get_from_terminal("pgrep vitrage-graph")
        if text_out2 != '':
            utils.run_from_terminal("kill -9 " + text_out2)
