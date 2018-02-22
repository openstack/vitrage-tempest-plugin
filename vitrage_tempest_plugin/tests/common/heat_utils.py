# Copyright 2017 - Nokia
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
import time

from heatclient.common import http
from heatclient.common import template_utils

from vitrage_tempest_plugin.tests.common.tempest_clients import TempestClients
from vitrage_tempest_plugin.tests.utils import wait_for_status


def create_stacks(num_stacks, nested, template_file):
    tpl_files, template = template_utils.process_template_path(
        template_file,
        object_request=http.authenticated_fetcher(TempestClients.heat()))

    for i in range(num_stacks):
        stack_name = 'stack_%s' % i + ('_nested' if nested else '')
        TempestClients.heat().stacks.create(stack_name=stack_name,
                                            template=template,
                                            files=tpl_files,
                                            parameters={})
        wait_for_status(45,
                        _check_num_stacks,
                        num_stacks=num_stacks,
                        state='CREATE_COMPLETE')
        time.sleep(2)


def delete_all_stacks():
    stacks = TempestClients.heat().stacks.list()
    for stack in stacks:
        try:
            TempestClients.heat().stacks.delete(stack.to_dict()['id'])
        except Exception:
            pass

    wait_for_status(30, _check_num_stacks, num_stacks=0)
    time.sleep(4)


def _check_num_stacks(num_stacks, state=''):
    stacks_list = \
        [stack.to_dict() for stack in TempestClients.heat().stacks.list()
         if 'FAILED' not in stack.to_dict()['stack_status']]
    if len(stacks_list) != num_stacks:
        return False

    return all(stack['stack_status'].upper() == state.upper()
               for stack in stacks_list)
