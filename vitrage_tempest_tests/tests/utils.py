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
from vitrage import service

import os
import oslo_messaging
import re
import subprocess
import vitrage_tempest_tests.tests

extra_log_level_defaults = [
    'vitrage_tempest_tests.tests.utils=INFO',
    'vitrage_tempest_tests.tests.run_vitrage_env=INFO',
    'vitrage_tempest_tests.tests.stop_vitrage_env=INFO',
    'vitrage_tempest_tests.tests.api.topology.topology=INFO',
    'vitrage.api.controllers.v1.topology=WARN',
    'oslo_messaging._drivers.amqpdriver=WARN'
]

LOG = logging.getLogger(__name__)
CONF = cfg.CONF
logging.register_options(CONF)
logging.setup(CONF, "vitrage")
logging.set_defaults(default_log_levels=extra_log_level_defaults)


def opts():
    return [
        ('keystone_authtoken', vitrage_tempest_tests.tests.OPTS)
    ]


def get_from_terminal(command):
    proc = os.popen(command)
    text_out = proc.read()
    proc.close()
    LOG.debug("The command is : " + command)
    if text_out != '':
        LOG.debug("The command output is : \n" + text_out)
    return text_out


def run_vitrage_command(command):
    p = subprocess.Popen(command,
                         shell=True,
                         executable="/bin/bash",
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if stderr != '':
        LOG.error("The command output error is : " + stderr)
    if stdout != '':
        LOG.debug("The command output is : \n" + stdout)
        return stdout
    return None


def run_from_terminal(command):
    proc = os.popen(command)
    text_out = proc.read()
    proc.close()
    LOG.debug("The command is : " + command)
    if text_out != '':
        LOG.debug("The command output is : \n" + text_out)


def change_terminal_dir(path):
    os.chdir(path)
    LOG.debug("The path is : " + path)


def get_conf():
    conf = service.prepare_service([])
    for group, options in opts():
        conf.register_opts(list(options), group=group)
    return conf


def get_client():
    transport = oslo_messaging.get_transport(cfg.CONF)
    cfg.CONF.set_override('rpc_backend', 'rabbit')
    target = oslo_messaging.Target(topic='rpcapiv1')
    return oslo_messaging.RPCClient(transport, target)


def get_regex_from_array(pattern, lines_arr):
    p = re.compile(pattern)
    for line in lines_arr:
        m = p.search(line)
        if m:
            LOG.debug("The field value is " + m.group(1))
            return m.group(1)
    return None


def get_regex_result(pattern, text):
    p = re.compile(pattern)
    m = p.search(text)
    if m:
        LOG.debug("The regex value is " + m.group(1))
        return m.group(1)
    return None
