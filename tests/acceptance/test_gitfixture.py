# Copyright (c) 2018 Hewlett Packard Enterprise Development Company LP
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

from testtools import matchers

from fixtures_git.gitfixture import GitFixture
from tests import acceptance


class TestGitFixture(acceptance.BaseTestCase):

    def test_basic(self):
        gitfixture = self.useFixture(
            GitFixture(
                [['A', []],
                 ['B', ['A']],
                 ['C', ['B']],
                 ],
                [['master', 'C']],
            ),
        )
        nodes = gitfixture.gittree.graph

        self.assertEqual(len(list(gitfixture.repo.iter_commits())), 3)
        self.assertTrue(gitfixture.repo.is_ancestor(nodes['A'], nodes['C']))
        self.assertTrue(gitfixture.repo.is_ancestor(nodes['A'], nodes['B']))
        self.assertEqual(gitfixture.repo.commit('master'), nodes['C'])

    def test_merge(self):
        gitfixture = self.useFixture(
            GitFixture(
                [['A', []],
                 ['B', ['A']],
                 ['C', ['B']],
                 ['D', ['A']],
                 ['E', ['D']],
                 ['F', ['C', 'E']],
                 ]
            ),
        )
        nodes = gitfixture.gittree.graph

        self.assertTrue(gitfixture.repo.is_ancestor(nodes['B'], nodes['F']))
        self.assertTrue(gitfixture.repo.is_ancestor(nodes['D'], nodes['F']))
        self.assertEqual(len(gitfixture.repo.commit(nodes['F']).parents), 2)
        self.assertEqual(gitfixture.repo.merge_base(nodes['E'], nodes['C']),
                         [nodes['A']])

        node_f_files = gitfixture.repo.git.ls_files(
            with_tree=nodes['F']).split('\n')
        node_e_files = gitfixture.repo.git.ls_files(
            with_tree=nodes['E']).split('\n')
        node_c_files = gitfixture.repo.git.ls_files(
            with_tree=nodes['C']).split('\n')
        self.assertThat(
            sorted(node_f_files),
            matchers.NotEquals(sorted(node_c_files))
        )
        self.assertThat(
            sorted(node_f_files),
            matchers.Equals(sorted(set(node_c_files + node_e_files)))
        )

    def test_merge_and_replace(self):
        gitfixture = self.useFixture(
            GitFixture(
                [['A', []],
                 ['B', ['A']],
                 ['C', ['B']],
                 ['D', ['A']],
                 ['E', ['D']],
                 ['F', ['=C', 'E']],
                 ]
            ),
        )
        nodes = gitfixture.gittree.graph

        node_f_files = gitfixture.repo.git.ls_files(
            with_tree=nodes['F']).split('\n')
        node_c_files = gitfixture.repo.git.ls_files(
            with_tree=nodes['C']).split('\n')
        self.assertThat(
            sorted(node_f_files),
            matchers.Equals(sorted(node_c_files))
        )

    def test_unrelated_history(self):
        gitfixture = self.useFixture(
            GitFixture(
                [['A', []],
                 ['B', ['A']],
                 ['C', ['B']],
                 ['D', []],
                 ['E', ['D']],
                 ['F', ['C', 'E']],
                 ]
            ),
        )
        nodes = gitfixture.gittree.graph

        self.assertFalse(gitfixture.repo.is_ancestor(nodes['A'], nodes['D']))
        self.assertFalse(gitfixture.repo.is_ancestor(nodes['D'], nodes['A']))
        self.assertEqual(gitfixture.repo.merge_base(nodes['C'], nodes['E']),
                         [])

        node_f_files = gitfixture.repo.git.ls_files(
            with_tree=nodes['F']).split('\n')
        node_e_files = gitfixture.repo.git.ls_files(
            with_tree=nodes['E']).split('\n')
        node_c_files = gitfixture.repo.git.ls_files(
            with_tree=nodes['C']).split('\n')
        self.assertThat(
            sorted(node_f_files),
            matchers.Equals(sorted(set(node_c_files + node_e_files))
                            )
        )
