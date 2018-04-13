What is fixtures-git?
=====================

Fixtures git is an open source Python library that adheres to the
fixtures API defined by https://pypi.python.org/pypi/fixtures

It was initially developed as part of git-upstream_ tests to make it
easy to construct git repositories with various layouts rather than
trying to mock/stub git's behaviour.

It is intended to allow developers to define a git repo layout using
a list definition of the commit nodes.

To install:

.. code:: bash

    pip install fixtures-git

See also https://pypi.python.org/pypi/fixtures-git


You can also install directly from source:

.. code:: bash

    git clone https://git.openstack.org/openstack/fixtures-git.git
    cd fixtures-git
    pip install .

Developers
----------

Bug reports:

* https://bugs.launchpad.net/fixtures-git

Repository:

* https://git.openstack.org/cgit/openstack/fixtures-git

Cloning:

.. code:: bash

    git clone https://git.openstack.org/cgit/openstack/fixtures-git

or

.. code:: bash

    git clone https://github.com/openstack/fixtures-git

A virtual environment is recommended for development.  For example,
git-upstream may be installed from the top level directory:

.. code:: bash

    virtualenv .venv
    source .venv/bin/activate
    pip install -r test-requirements.txt -e .


Patches are submitted via Gerrit at:

* https://review.openstack.org/

Please do not submit GitHub pull requests, they will be automatically
closed.

More details on how you can contribute is available on the wiki at:

* http://docs.openstack.org/infra/manual/developers.html

Writing a patch
---------------

All code submissions must be pep8_ and pyflakes_ clean. CI will
automatically reject them if they are not. The easiest way to do that
is to run tox_ before submitting code for review in Gerrit. It will
run ``pep8`` and ``pyflakes`` in the same manner as the automated
test suite that will run on proposed patchsets.

Support
-------

Is via the git-upstream_ community which is is found on the
`#git-upstream channel on chat.freenode.net
<irc://chat.freenode.net/#git-upstream>`_

You can also join via this `IRC URL
<irc://chat.freenode.net/#git-upstream>`_ or use the `Freenode IRC
webchat <https://webchat.freenode.net/>`_.


.. _git-upstream: https://pypi.python.org/pypi/git-upstream
.. _pep8: https://pypi.python.org/pypi/pep8
.. _pyflakes: https://pypi.python.org/pypi/pyflakes
.. _tox: https://testrun.org/tox

