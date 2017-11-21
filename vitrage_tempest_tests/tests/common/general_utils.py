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
import six


def get_first_match(list_of_dicts, subset_dict):
    for d in list_of_dicts:
        if is_subset(subset_dict, d):
            return d


def get_all_matchs(list_of_dicts, subset_dict):
    # TODO(idan_hefetz) this method can replace the notorious
    # TODO(idan_hefetz) '_filter_list_by_pairs_parameters'
    return [d for d in list_of_dicts if is_subset(subset_dict, d)]


def is_subset(subset, full):
    return six.viewitems(subset) <= six.viewitems(full)
