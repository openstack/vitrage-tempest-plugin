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

from functools import wraps

import socket
import time

from oslo_config.cfg import NoSuchOptError
from oslo_log import log as logging

import os
import re
import subprocess

LOG = logging.getLogger(__name__)


def get_from_terminal(command):
    proc = os.popen(command)
    text_out = proc.read()
    proc.close()
    return text_out


def run_vitrage_command(command, conf):
    # AUTH_URL
    local_ip = socket.gethostbyname(socket.gethostname())
    auth_url = get_property_value('OS_AUTH_URL', 'auth_url',
                                  'http://%s:5000/v2.0' % local_ip, conf)
    auth_url_param = '--os-auth-url ' + auth_url

    # USERNAME
    user = get_property_value('OS_USERNAME', 'username',
                              'admin', conf)
    user_param = '--os-user-name ' + user

    # PASSWORD
    password = get_property_value('OS_PASSWORD', 'password',
                                  'secretadmin', conf)
    password_param = '--os-password ' + password

    # PROJECT_NAME
    project_name = get_property_value('OS_TENANT_NAME', 'project_name',
                                      'admin', conf)
    project_name_param = '--os-project-name ' + project_name

    # USER_DOMAIN_ID
    user_domain_id = get_property_value('OS_USER_DOMAIN_ID',
                                        'user_domain_id',
                                        'default', conf)
    user_domain_id_param = '--os-user-domain-id ' + user_domain_id

    # PROJECT_DOMAIN_ID
    project_domain_id = get_property_value('OS_PROJECT_DOMAIN_ID',
                                           'project_domain_id',
                                           'default', conf)
    project_domain_id_par = '--os-project-domain-id ' + project_domain_id

    full_command = '%s %s %s %s %s %s %s' % (command, user_param,
                                             password_param,
                                             project_name_param,
                                             auth_url_param,
                                             user_domain_id_param,
                                             project_domain_id_par)

    LOG.info('Full command: %s', full_command)

    child = subprocess.Popen(full_command,
                             shell=True,
                             executable="/bin/bash",
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

    stdout, stderr = child.communicate()
    if stderr:
        LOG.error('error from command %(command)s = %(error)s',
                  {'error': stderr, 'command': full_command})

    output = stdout.decode('utf-8')

    LOG.info('cli stdout: %s', output)

    if child.returncode:
        LOG.error('process return code is not 0 : return code = %d',
                  child.returncode)
    return output


def get_property_value(environment_name, conf_name, default_value, conf):
    if os.environ.get(environment_name):
        return os.environ[environment_name]

    try:
        return conf.service_credentials[conf_name]
    except NoSuchOptError:
        LOG.debug("Configuration doesn't exist: service_credentials.%s",
                  conf_name)

    return default_value


def run_from_terminal(command):
    proc = os.popen(command)
    proc.close()


def change_terminal_dir(path):
    os.chdir(path)
    LOG.debug("The path is : " + path)


def get_regex_result(pattern, text):
    p = re.compile(pattern)
    m = p.search(text)
    if m:
        LOG.debug("The regex value is " + m.group(1))
        return m.group(1)
    return None


def uni2str(text):
    return text.encode('ascii', 'ignore')


def tempest_logger(func):
    func_name = func.__name__

    @wraps(func)
    def func_name_print_func(*args, **kwargs):
        LOG.info('Test Start: ' + func_name)
        result = func(*args, **kwargs)
        LOG.info('Test End: ' + func_name)
        return result

    return func_name_print_func


def wait_for_answer(max_waiting, time_between_attempts, func, **kwargs):
    """time_between_attempts should be in range of 0 to 1"""
    status, res = False, None
    start_time = time.time()
    while time.time() - start_time < max_waiting:
        time.sleep(time_between_attempts)
        status, res = func(**kwargs)
        if status:
            return res
    LOG.info("wait for answer- False")
    return res


def wait_for_status(max_waiting, func, **kwargs):
    count = 0
    while count < max_waiting:
        if func(**kwargs):
            return True
        count += 1
        time.sleep(2)
    LOG.error("wait_for_status - False")
    return False


def filter_data(data, filter_, match_filter=True):
    if match_filter:
        return {k for k in data if k in filter_}
    return {k for k in data if k not in filter_}
