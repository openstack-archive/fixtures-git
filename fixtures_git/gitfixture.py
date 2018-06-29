# Copyright (c) 2013-2016 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2018 Hewlett Packard Enterprise Development Company LP
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

import faker
import os
import shutil
import tempfile

import fixtures
import git

from fixtures_git import utils


class GitTree(object):
    """Helper class to build a git repository from a graph definition

    Helper class to build a git repository from a graph definition of
    nodes and their parent nodes. A list of branches may be provided
    where each element has two members corresponding to the name and the
    target node it references.

    Supports unordered graphs, only requirement is that there is a commit
    defined with no parents, which will become the root commit.

    Root commits can specified by an empty list as the second member:

        ('NodeA', [])

    Merge commits are specified by multiple nodes:

        ('NodeMerge', ['Node1', 'Node2'])


    An '=' prefix can be used in front of one of the parents of a merge
    commit to indicate that the merge commit's tree should be copied
    directly from that parent ignoring any contributions from the other
    parents' trees (like what git enables with the '-s ours' merge
    strategy.

    This is used when needing to preserve history but not interested in
    the changes from the other branches. One tool that makes extensive
    usage of this is _git-upstream.

    E.g., the following will result in a merge commit 'C', with parents
    'P1' and 'P2', but will have the same tree as 'P1'.

        ('C', ['=P1', 'P2'])


    The tree building code can handle a graph definition being out of
    order but will fail to find certain circular dependencies and may
    result in an infinite loop.

    Examples:

        [('A', []), ('B', ['A']), ('C', ['B'])]
        [('A', []), ('C', ['B']), ('B', ['A'])]

    .. _git-upstream: https://pypi.python.org/pypi/git-upstream
        """

    def __init__(self, gitrepo, tree, branches):
        self.graph = {}
        self.gitrepo = gitrepo
        self.repo = gitrepo.repo
        self._build_git_tree(tree, branches)

    def _commit(self, node):
        p_node = utils._get_node_to_pick(node)
        if p_node:
            self.repo.git.cherry_pick(self.graph[p_node], x=True)
        else:
            # standard commit
            self.gitrepo.add_commits(1, ref="HEAD",
                                     message_prefix="[%s]" % node)

    def _merge_commit(self, node, parents):
        # merge commits
        parent_nodes = [p.lstrip("=") for p in parents]
        commits = [str(self.graph[p]) for p in parent_nodes[1:]]

        if any([p.startswith("=") for p in parents]):
            # special merge commit using inverse of 'ours' by
            # emptying the current index and then reading in any
            # trees of the nodes prefixed with '='
            use = [str(self.graph[p.lstrip("=")])
                   for p in parents if p.startswith("=")]
            try:
                self.repo.git.merge(*commits, s="ours", no_commit=True)
            except git.exc.GitCommandError as exc:
                if 'refusing to merge unrelated histories' in exc.stderr:
                    self.repo.git.merge(*commits, s="ours", no_commit=True,
                                        allow_unrelated_histories=True)
                else:
                    raise
            self.repo.git.read_tree(empty=True)
            self.repo.git.read_tree(empty=True)
            self.repo.git.read_tree(*use, u=True, reset=True)
        elif len(commits) < 2:
            # standard merge
            try:
                self.repo.git.merge(*commits, no_commit=True)
            except git.exc.GitCommandError as exc:
                if 'refusing to merge unrelated histories' in exc.stderr:
                    self.repo.git.merge(*commits, no_commit=True,
                                        allow_unrelated_histories=True)
                else:
                    raise
        else:
            # multi-branch merge, git is not great at handling
            # merging multiple orphaned branches
            try:
                self.repo.git.merge(*commits, s="ours", no_commit=True)
            except git.exc.GitCommandError as exc:
                if 'refusing to merge unrelated histories' in exc.stderr:
                    self.repo.git.merge(*commits, s="ours", no_commit=True,
                                        allow_unrelated_histories=True)
                else:
                    raise
            self.repo.git.read_tree(empty=True)
            self.repo.git.read_tree("HEAD", *commits)
            self.repo.git.checkout("--", ".")
        self.repo.git.commit(m="[%s] Merging %s into %s" %
                               (node, ",".join(parent_nodes[1:]),
                                parent_nodes[0]))
        self.repo.git.clean(f=True, d=True, x=True)

    def _build_git_tree(self, graph_def, branches=[]):

        # require that graphs must have at least 1 node with no
        # parents, which is a root commit in git
        if not any([True for _, parents in graph_def if not parents]):
            assert("No root commit defined in test graph")

        for node, parents in utils._reverse_toposort(graph_def):
            if not parents:
                # root commit
                self.repo.git.symbolic_ref("HEAD", "refs/heads/%s" % node)
                self.repo.git.rm(".", r=True, cached=True,
                                 with_exceptions=False)
                self.repo.git.clean(f=True, d=True, x=True)
                self.gitrepo.add_commits(1, ref="HEAD",
                                         message_prefix="[%s]" % node)
                # only explicitly listed branches should exist afterwards
                self.repo.git.checkout(self.repo.commit())
                self.repo.git.branch(node, D=True)

            else:
                # checkout the dependent node
                self.repo.git.checkout(self.graph[parents[0].lstrip('=')])
                if len(parents) > 1:
                    # merge commits
                    self._merge_commit(node, parents)
                else:
                    self._commit(node)
            self.graph[node] = self.repo.commit()

        for name, node in branches:
            self.repo.git.branch(name, str(self.graph[node]), f=True)

        # return to master
        self.repo.git.checkout("master")

    def commits_from_nodes(self, nodes=[]):

        return [self.graph[n] for n in nodes]


class GitFixture(fixtures.Fixture):
    """Create a git repo in which to operate.

    By default creates an empty git repository under a temporary
    directory and deletes it after use.

    It accepts options to automatically define a git repository
    layout based on list of commits setting the given branches to
    the relevant node once built.

    :ivar graph: Iterable describing the tree of git commits to create.
    :ivar branches: Dict of node to branch names to set once finished.
    :ivar path: Custom path to use, otherwise will create a temporary
        directory to use and set the 'path' attribute to it.
    :ivar user: Dict describing a user to use for commits, defaults
        to 'Example User <user@example.com>',
    :ivar clean_on_exit: Control whether to delete the tempoary path
        once complete, defaults to 'True', but is ignored if 'path'
        is provided.
    """

    def __init__(self, graph=None, branches=None, path=None, user=None,
                 clean_on_exit=True):
        # set attributes for use
        self.path = path
        self.gittree = None
        self.repo = None

        # internal attributes
        self._graph = graph or []
        self._branches = branches or []
        self._user = {
            'name': 'Example User',
            'email': 'user@example.com',
        }
        self._user.update(user or {})

        self._clean_on_exit = clean_on_exit
        # for text generation
        self._faker = faker.Faker()

    def _setUp(self):
        self._file_list = set()
        if not self.path:
            tempdir = self.useFixture(fixtures.TempDir())
            self.path = os.path.join(tempdir.path, 'git')
            if self._clean_on_exit is True:
                self.addCleanup(shutil.rmtree, tempdir.path)

        os.mkdir(self.path)
        g = git.Git(self.path)
        g.init()

        self.repo = git.Repo(self.path)
        self.repo.git.config('user.email', self._user['email'])
        self.repo.git.config('user.name', self._user['name'])
        self.repo.git.commit(m="Initialize empty repo", allow_empty=True)

        if self._graph:
            self.gittree = GitTree(self, self._graph, self._branches)

    def _create_file(self):
        contents = "\n\n".join(self._faker.paragraphs(3))

        # always want to ensure the files added to the repo are unique no
        # matter which branch they are added to, as otherwise there may
        # be conflicts caused by replaying local changes and performing
        # merges
        while True:
            tmpfile = tempfile.NamedTemporaryFile(
                dir=self.repo.working_dir, delete=False)
            if tmpfile.name not in self._file_list:
                self._file_list.add(tmpfile.name)
                break
            # case where same filename in use on a different branch
            tmpfile.close()
            os.remove(tmpfile.name)

        tmpfile.write(contents.encode('utf-8'))
        tmpfile.close()
        return tmpfile.name

    def _create_file_commit(self, change_id=None, message_prefix=None):
        filename = self._create_file()
        self.repo.git.add(filename)
        message = "Adding %s" % os.path.basename(filename)
        if message_prefix:
            message = "%s %s" % (message_prefix, message)
        if change_id:
            message = message + "\n\nChange-Id: %s" % change_id
        self.repo.git.commit(m=message)

    def add_commits(self, num=None, ref="HEAD", change_ids=[],
                    message_prefix=None):
        """Create the given number of commits using generated files"""
        if ref != "HEAD":
            self.repo.git.checkout(ref)

        if num is None:
            num = max(1, len(change_ids))
        ids = list(change_ids) + [None] * (num - len(change_ids))

        for x in range(num):
            self._create_file_commit(
                change_id=ids[x], message_prefix=message_prefix)
