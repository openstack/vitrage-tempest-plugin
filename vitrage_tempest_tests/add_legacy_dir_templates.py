# Copyright 2017 - Nokia
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import sys

from vitrage.common.constants import TemplateStatus
from vitrage.common.constants import TemplateTypes as TType
from vitrage.evaluator.template_db.template_repository import \
    add_template_to_db
from vitrage import service
from vitrage import storage
from vitrage_tempest_tests.tests.common import general_utils

files = ['corrupted_template.yaml', 'e2e_test_basic_actions.yaml',
         'e2e_test_overlapping_actions.yaml', 'v1_execute_mistral.yaml',
         'v2_execute_mistral.yaml', 'host_aodh_alarm_for_rca.yaml',
         'nagios_alarm_for_alarms.yaml'
         ]


def main():
    resources_path = general_utils.tempest_resources_dir() + '/templates/api/'
    conf = service.prepare_service()
    db = storage.get_connection_from_config(conf)
    for f in files:
        full_path = resources_path + f
        template = add_template_to_db(db, full_path, TType.STANDARD)
        if template[0]['name'] != 'corrupted_template':
            db.templates.update(template[0]['uuid'],
                                'status', TemplateStatus.ACTIVE)

if __name__ == "__main__":
    sys.exit(main())
