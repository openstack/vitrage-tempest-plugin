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
from os import path
import six


def first_match(list_of_dicts, **kwargs):
    subset_dict = _remove_none_values(**kwargs)
    for d in list_of_dicts:
        if is_subset(subset_dict, d):
            return d


def all_matches(list_of_dicts, **kwargs):
    subset_dict = _remove_none_values(**kwargs)
    return [d for d in list_of_dicts if is_subset(subset_dict, d)]


def is_subset(subset, full):
    if not subset:
        return True
    full_dict = full
    if type(full) is not dict:
        full_dict = full.__dict__
    return six.viewitems(subset) <= six.viewitems(full_dict)


def _remove_none_values(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


def tempest_resources_dir():
    return path.join(path.dirname(path.dirname(__file__)), 'resources')
