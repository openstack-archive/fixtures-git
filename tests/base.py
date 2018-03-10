# Copyright (c) 2018 Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


class IsOrderedSubsetOfMismatch(object):
    def __init__(self, subset, set):
        self.subset = list(subset)
        self.set = list(set)

    def describe(self):
        return "set %r is not an ordered subset of %r" % (
            self.subset, self.set)

    def get_details(self):
        return {}


class IsOrderedSubsetOf(object):
    """Matches if the actual matches the order of iterable."""

    def __init__(self, iterable):
        self.iterable = iterable

    def __str__(self):
        return 'IsOrderedSubsetOf(%s)' % self.iterable

    def match(self, actual):
        iterable = iter(self.iterable)
        if all(item in iterable for item in actual):
            return None
        else:
            return IsOrderedSubsetOfMismatch(actual, self.iterable)
