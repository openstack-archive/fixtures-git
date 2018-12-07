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

import itertools
import random
import string
import time

import fixtures
import github3 as github

try:
    import urlparse as parse
except ImportError:
    from urllib import parse

TEST_REPO_DESC = "########## Auto-generated test repository ##########"


class GithubLoginMixin(object):

    def login(self, token, url=None):

        if url is None:
            url = "https://github.com"

        if parse.urlparse(url).netloc == "github.com":
            return github.login(token=token)
        else:
            return github.enterprise_login(token=token, url=url)


class GithubRepoFixture(GithubLoginMixin, fixtures.Fixture):
    """
    Fixture to create a new repo in GitHub and remove once finished.
    """

    default_repo_name_template = 'workflow-test-XXXXXX'

    def __init__(self, owner, token, url=None, name_template=None):

        super(GithubRepoFixture, self).__init__()

        self.owner = owner
        self.name_template = name_template or self.default_repo_name_template

        self.repo = None
        self.repo_name = None

        # use GithubLoginMixin
        self.github = self.login(token, url)

        # try an auth'ed request to make sure we have a valid token
        # note this requires the token to have read on user
        self.me = self.github.me()

    def _setUp(self):

        # allow user to provide an exact name to use
        if self.repo_name is None:
            # handle template_name missing 'XXXXX' result in it containing
            # a single element so set suffix to '' in that case.
            template_parts = iter(self.name_template.split('XXXXXX'))
            prefix = next(template_parts)
            suffix = next(template_parts, '')

            self.repo_name = ''.join(
                itertools.chain(
                    prefix,
                    (random.choice(string.ascii_uppercase + string.digits)
                    for _ in range(8)),
                    suffix
                )
            )

        self.addCleanup(self._delete_repo)

        org = self.github.organization(self.owner)
        self.repo = org.create_repository(
            name=self.repo_name,
            description=TEST_REPO_DESC,
            has_issues=False,
            has_wiki=False,
            auto_init=True,
        )

    def _delete_repo(self):
        if self.repo is not None:
            self.repo.delete()
        elif self.repo_name is not None:
            repo = self.github.repository(self.owner, self.repo_name)
            if repo:
                repo.delete()


class GithubForkedRepoFixture(GithubLoginMixin, fixtures.Fixture):
    """
    Fixture to create and delete a fork of the given repo in the
    default GitHub org of the token user
    """
    def __init__(self, src_repo, token, url=None):

        super(GithubForkedRepoFixture, self).__init__()

        self.src_repo = src_repo

        self.repo = None

        # use GithubLoginMixin
        self.github = self.login(token, url)

        # try an auth'ed request to make sure we have a valid token
        # note this requires the token to have read on user
        self.me = self.github.me()

    def _setUp(self):
        owner, repo_name = self.src_repo.split('/')
        upstream_repo = self.github.repository(owner, repo_name)

        self.addCleanup(self._delete_repo)
        self.repo = upstream_repo.create_fork()
        # wait for the fork to be available
        while self.github.repository(self.me, repo_name) is None:
            time.sleep(2)

    def _delete_repo(self):
        repo_name = self.src_repo.split('/')[-1]
        repo = self.github.repository((self.github.me()).login, repo_name)
        if repo and repo.description == TEST_REPO_DESC:
            repo.delete()
