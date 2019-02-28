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

import time

from oslo_log import log as logging
from tempest.common import credentials_factory as common_creds
from tempest import config

import subprocess

CONF = config.CONF
LOG = logging.getLogger(__name__)

TIMESTAMP_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def run_vitrage_command(command):
    admin_creds = common_creds.get_configured_admin_credentials()

    auth_url = CONF.identity.uri_v3
    auth_url_param = '--os-auth-url ' + auth_url

    # USERNAME
    user = admin_creds.username
    user_param = '--os-user-name ' + user

    # PASSWORD
    password = admin_creds.password
    password_param = '--os-password ' + password

    # PROJECT_NAME
    project_name = admin_creds.project_name
    project_name_param = '--os-project-name ' + project_name

    # USER_DOMAIN_ID
    user_domain_id = admin_creds.user_domain_id
    user_domain_id_param = '--os-user-domain-id ' + user_domain_id

    # PROJECT_DOMAIN_ID
    project_domain_id = admin_creds.project_domain_id
    project_domain_id_par = '--os-project-domain-id ' + project_domain_id

    full_command = '%s %s %s %s %s %s %s' % (command, user_param,
                                             password_param,
                                             project_name_param,
                                             auth_url_param,
                                             user_domain_id_param,
                                             project_domain_id_par)

    LOG.debug('Full command: %s', full_command)

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

    LOG.debug('cli stdout: %s', output)

    if child.returncode:
        LOG.error('process return code is not 0 : return code = %d',
                  child.returncode)
    return output


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
