.. image:: https://gitlab.com/myqueue/myqueue/badges/master/coverage.svg
.. image:: https://badge.fury.io/py/myqueue.svg
    :target: https://pypi.org/project/myqueue/
.. image:: https://joss.theoj.org/papers/10.21105/joss.01844/status.svg
    :target: https://doi.org/10.21105/joss.01844
.. image:: https://readthedocs.org/projects/myqueue/badge/?version=latest
    :target: https://myqueue.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

=======
MyQueue
=======

MyQueue is a tool for submitting and keeping track of tasks running on a
cluster of computers. It uses SLURM_, PBS_ or LSF_ as a backend and makes
handling of tasks easy. It has a command-line interface called *mq* with a
number of sub-commands and a Python interface for managing workflows.  Simple
to set up: no system administrator or database required.

.. admonition:: Features

    * Easy task submission:

      * from the command line: ``mq submit <task> -R <cores>:<time>``
      * from Python: ``myqueue.submit(...)``

    * Automatic restarting of timed-out/out-of-memory tasks
      with more time/cores

    * Remembers your finished and failed tasks

    * Powerful *list* command for monitoring

    * Can be used together with Python *venv*\ 's

    * Folder-based Workflows

Quick links:

* Documentation: https://myqueue.readthedocs.io/
* Code: https://gitlab.com/myqueue/myqueue/
* Issues: https://gitlab.com/myqueue/myqueue/issues/
* Chat: https://matrix.to/#/#myqueue:matrix.org


.. _SLURM: https://slurm.schedmd.com/
.. _PBS: https://en.m.wikipedia.org/wiki/Portable_Batch_System
.. _LSF: https://en.m.wikipedia.org/wiki/Platform_LSF


Examples
--------

Submit Python script to 32 cores for 2 hours::

    $ mq submit script.py -R 32:2h

Submit Python module *abc.run* in two folders::

    $ mq submit abc.run F1/ F2/ -R 16:30m

Check results of tasks in current folder and its sub-folders::

    $ mq list  # or mq ls
    id  folder name      res.   age     state   time    error
    --- ------ --------- ------ ------- ------- ------- ------
    117 ./     script.py 32:2h  5:28:43 TIMEOUT 2:00:03
    118 ./F1/  abc.run   16:30m 5:22:16 done      12:12
    119 ./F2/  abc.run   16:30m 5:22:16 done      17:50
    --- ------ --------- ------ ------- ------- ------- ------
    done: 2, TIMEOUT: 1, total: 3

Resubmit with more resources (1 day)::

     $ mq resubmit -i 117 -R 32:1d

See more examples of use here:

* `Quick-start
  <https://myqueue.readthedocs.io/en/latest/quickstart.html>`__
* `Documentation
  <https://myqueue.readthedocs.io/en/latest/documentation.html>`__
* `How it works
  <https://myqueue.readthedocs.io/en/latest/howitworks.html>`__
* `Command-line interface
  <https://myqueue.readthedocs.io/en/latest/cli.html>`__
* `Workflows
  <https://myqueue.readthedocs.io/en/latest/workflows.html>`__
* `Python API
  <https://myqueue.readthedocs.io/en/latest/api.html>`__


Installation
============

MyQueue has only one dependency: Python_ version 3.7 or later.

Install MyQueue from PyPI_ with *pip*::

    $ python3 -m pip install myqueue

Enable bash tab-completion for future terminal sessions like this::

    $ mq completion >> ~/.profile

Now, configure your system as described
`here <https://myqueue.readthedocs.io/en/latest/configuration.html>`__.


.. _Python: https://python.org/
.. _PyPI: https://pypi.org/project/myqueue/


Release notes
=============

See the `release notes
<https://myqueue.readthedocs.io/en/latest/releasenotes.html>`_ for a history
of notable changes to MyQueue.


Help, support and feedback
==========================

If you need help, want to report a bug or suggest a new feature then you are
welcome to get in touch via MyQueue's `issue tracker`_
or the *#myqueue* room on Matrix_.

.. _issue tracker: https://gitlab.com/myqueue/myqueue/issues/
.. _Matrix: https://matrix.to/#/#myqueue:matrix.org


Contributing
============

We welcome contributions to the code and documentation, preferably as
`merge-requests <https://gitlab.com/myqueue/myqueue/merge_requests/>`_.
More information `here
<https://myqueue.readthedocs.io/en/latest/development.html>`_.
