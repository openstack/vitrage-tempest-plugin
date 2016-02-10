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

import os
import re
import testtools

LOG = logging.getLogger(__name__)


class RunVitrageEnv(testtools.TestCase):
    """RunVitrageEnv class. Run Vitrage env."""

    def __init__(self, *args, **kwds):
        super(RunVitrageEnv, self).__init__(*args, **kwds)
        self.filename = '/opt/stack/vitrage/etc/vitrage/vitrage.conf'
        self.port = '8999'

    def test_run_env(self):
        self._set_env_params()
        print("The host ip address = " + self.host + " with port " + self.port)

        LOG.info('MARINA!!!')
        if self._show_vitrage_processes() is True:
            print ("The vitrage processed existed and should be removed")
            LOG.info('The vitrage processed existed and should be removed')
            self._stop_vitrage_processes()

        os.system("openstack service create rca" +
                  " --os-username " + self.user +
                  " --os-password " + self.password +
                  " --os-auth-url " + self.url +
                  " --os-project-name admin" +
                  " --name vitrage")
        os.system("openstack endpoint create rca --os-username " + self.user +
                  " --os-password " + self.password +
                  " --os-auth-url " + self.url +
                  " --os-project-name admin" +
                  " --adminurl http://" + self.host + ":" + self.port +
                  " --internalurl http://" + self.host + ":" + self.port +
                  " --publicurl http://" + self.host + ":" + self.port +
                  " --region RegionOne")

        os.chdir('/tmp')
        os.system("\rm nohup.out")
        os.system("nohup vitrage-graph &")
        os.system("nohup vitrage-api &")

        if self._show_vitrage_processes() is False:
            LOG.error("No vitrage processes founded")
            raise ValueError("No vitrage processes founded")

        if self._validate_vitrage_processes() is False:
            LOG.error("The vitrage processes are not correct")
            self._stop_vitrage_processes()
            raise ValueError("The vitrage processes are not correct")

    @staticmethod
    def _show_vitrage_processes():
        text_out = os.popen(
            "ps -ef | grep vitrage-api | grep -v grep").read()
        print (text_out)

        text_out2 = os.popen(
            "ps -ef | grep vitrage-graph | grep -v grep").read()
        print (text_out2)

        if ("vitrage-api" in text_out) and ("vitrage-graph" in text_out2):
            LOG.info('The vitrage processes exists')
            return True
        elif "vitrage-api" in text_out:
            LOG.info('Only vitrage-api process exist')
            return True
        elif "vitrage-graph" in text_out2:
            LOG.info('Only vitrage-graph process exist')
            return True
        else:
            LOG.info('The vitrage process does not run')
            return False

    @staticmethod
    def _get_field_from_file(pattern, lines_arr):
        p = re.compile(pattern)
        for line in lines_arr:
            m = p.search(line)
            if m:
                print("The field value is " + m.group(1))
                return m.group(1)
        return None

    def _set_env_params(self):
        lines_arr = []
        with open(self.filename, 'r') as the_file:
            for line in the_file:
                if "#" not in line and line.strip() != '':
                    lines_arr.append(line)

        self.user = self._get_field_from_file(
            "admin_user = (\w+)", lines_arr)
        text_out = os.popen("echo $OS_USERNAME").read()
        if text_out not in self.user:
            os.system("export OS_USERNAME=" + self.user)

        self.tenent_user = self._get_field_from_file(
            "admin_tenant_name = (\w+)", lines_arr)
        text_out = os.popen("echo $OS_TENANT_NAME").read()
        if text_out not in self.tenent_user:
            os.system("export OS_TENANT_NAME=" + self.tenent_user)

        self.password = self._get_field_from_file(
            "admin_password = (\w+)", lines_arr)
        text_out = os.popen("echo $OS_PASSWORD").read()
        if text_out not in self.password:
            os.system("export OS_PASSWORD=" + self.password)

        self.host = self._get_field_from_file(
            "(\d+\.\d+\.\d+\.\d+)", lines_arr)
        self.url = "http://" + self.host + ":5000/v2.0"
        text_out = os.popen("echo $OS_AUTH_URL").read()
        if text_out not in self.url:
            os.system("export OS_AUTH_URL=" + self.url)

    @staticmethod
    def _stop_vitrage_processes():
        text_out = os.popen("pgrep vitrage-api").read()
        print (text_out)
        if text_out != '':
            LOG.info("The vitrage-api process exist")
            os.system("kill -9 " + text_out)

        text_out2 = os.popen("pgrep vitrage-graph").read()
        print (text_out2)
        if text_out2 != '':
            LOG.info("The vitrage-graph process exist")
            os.system("kill -9 " + text_out2)

    @staticmethod
    def _validate_vitrage_processes():
        text_out2 = os.popen("grep 'ERROR vitrage' nohup.out").read()
        if text_out2 != '':
            LOG.info("The error is : " + text_out2)
            print("The error is : " + text_out2)
            return False
        return True
