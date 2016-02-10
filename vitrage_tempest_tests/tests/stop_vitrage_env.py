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
import subprocess
import testtools

LOG = logging.getLogger(__name__)


class StopVitrageEnv(testtools.TestCase):
    """RunVitrageEnv class. Run Vitrage env."""

    def __init__(self, *args, **kwds):
        super(StopVitrageEnv, self).__init__(*args, **kwds)
        self.filename = '/etc/vitrage/vitrage.conf'

    @staticmethod
    def test_stop_vitrage_processes():
        f = subprocess.Popen("pgrep vitrage-api",
                             stdout=subprocess.PIPE, shell=True)
        text_out, std_error = f.communicate()
        print (text_out)
        if text_out != '':
            os.system("kill -9 " + text_out)

        f = subprocess.Popen("pgrep vitrage-graph",
                             stdout=subprocess.PIPE, shell=True)
        text_out, std_error2 = f.communicate()
        print (text_out)
        if text_out != '':
            os.system("kill -9 " + text_out)
