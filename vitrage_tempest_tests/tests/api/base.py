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
from vitrage.tests.base import BaseTest
from vitrage_tempest_tests.tests.base_mock import BaseMock

LOG = logging.getLogger(__name__)


class BaseVitrageTest(BaseTest):
    """Base test class for Vitrage API tests."""

    def __init__(self, *args, **kwds):
        super(BaseVitrageTest, self).__init__(*args, **kwds)

    def _create_graph_by_mock(self):
        """Create MOCK Graph and copied to the string """
        processor = BaseMock.create_processor_with_graph()
        entity_graph = processor.entity_graph
        mock_graph_output = entity_graph.output_graph()
        LOG.info("The mock graph is : " + mock_graph_output)
