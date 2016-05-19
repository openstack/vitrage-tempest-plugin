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

import socket

from oslo_config import cfg
from oslo_log import log as logging
from vitrage import service

import os
import oslo_messaging
import re
import subprocess
import vitrage_tempest_tests.tests

LOG = logging.getLogger(__name__)


def opts():
    return [
        ('keystone_authtoken', vitrage_tempest_tests.tests.OPTS)
    ]


def get_from_terminal(command):
    proc = os.popen(command)
    text_out = proc.read()
    proc.close()
    return text_out


def run_vitrage_command(command):
    local_ip = socket.gethostbyname(socket.gethostname())
    auth_url = os.environ['OS_AUTH_URL'] if \
        os.environ.get('OS_AUTH_URL') else 'http://%s:5000/v2.0' % local_ip
    auth_url_param = '--os-auth-url ' + auth_url

    user = os.environ['OS_USERNAME'] if \
        os.environ.get('OS_USERNAME') else 'admin'
    user_param = '--os-user-name ' + user

    password = os.environ['OS_PASSWORD'] if \
        os.environ.get('OS_PASSWORD') else 'secretadmin'
    password_param = '--os-password ' + password

    project_name = os.environ['OS_TENANT_NAME'] if \
        os.environ.get('OS_TENANT_NAME') else 'admin'
    project_name_param = '--os-project-name ' + project_name

    full_command = '%s %s %s %s %s' % (command, user_param, password_param,
                                       project_name_param, auth_url_param)

    LOG.info('Full command: %s', full_command)

    p = subprocess.Popen(full_command,
                         shell=True,
                         executable="/bin/bash",
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    return stdout


def run_from_terminal(command):
    proc = os.popen(command)
    proc.close()


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
