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

import testtools

from fixtures_git import utils
from tests import base


class TestResolve(testtools.TestCase):

    def test_ordered(self):
        nodes = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
        ]
        self.assertEqual(
            nodes,
            list(utils._reverse_toposort(nodes)),
        )

    def test_unordered(self):
        nodes = [
            ('B', ['A']),
            ('C', ['B']),
            ('A', []),
        ]
        self.assertEqual(
            [('A', []), ('B', ['A']), ('C', ['B'])],
            list(utils._reverse_toposort(nodes))
        )

    def test_merge(self):
        nodes = [
            ('B', ['A']),
            ('C', ['B']),
            ('A', []),
            ('E', ['D', 'C']),
            ('D', ['A']),
        ]
        sorted = list(utils._reverse_toposort(nodes))
        self.assertThat(
            (nodes[2], nodes[0], nodes[1], nodes[3]),
            base.IsOrderedSubsetOf(sorted)
        )
        self.assertThat(
            (nodes[2], nodes[4], nodes[3]),
            base.IsOrderedSubsetOf(sorted)
        )

    def test_multiple_merges(self):
        nodes = [
            ('B', ['A']),
            ('C', ['B']),
            ('A', []),
            ('E', ['D', 'C']),
            ('D', ['A']),
            ('G', ['F', 'C']),
            ('F', ['A']),
        ]
        sorted = list(utils._reverse_toposort(nodes))
        # A -> B -> C -> E
        self.assertThat(
            (nodes[2], nodes[0], nodes[1], nodes[3]),
            base.IsOrderedSubsetOf(sorted)
        )
        # A -> D -> E
        self.assertThat(
            (nodes[2], nodes[4], nodes[3]),
            base.IsOrderedSubsetOf(sorted)
        )
        # A -> F -> G
        self.assertThat(
            (nodes[2], nodes[6], nodes[5]),
            base.IsOrderedSubsetOf(sorted)
        )
        # A -> B -> C -> G
        self.assertThat(
            (nodes[2], nodes[0], nodes[1], nodes[5]),
            base.IsOrderedSubsetOf(sorted)
        )

    def test_merge_multiple_roots(self):
        nodes = [
            ('B', ['A']),
            ('C', []),  # root commit
            ('A', []),  # root commit
            ('D', ['B', 'C']),
        ]
        sorted = list(utils._reverse_toposort(nodes))
        # assert partial ordering because nodes A & B may come
        # before or after node C. Just make sure that node D
        # is defined after them.
        self.assertThat(
            (nodes[2], nodes[0], nodes[3]),
            base.IsOrderedSubsetOf(sorted),
        )
        self.assertThat(
            (nodes[1], nodes[3]),
            base.IsOrderedSubsetOf(sorted),
        )
