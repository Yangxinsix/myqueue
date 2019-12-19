.. image:: https://gitlab.com/myqueue/myqueue/badges/master/coverage.svg
.. image:: https://badge.fury.io/py/myqueue.svg
    :target: https://pypi.org/project/myqueue/

=======
MyQueue
=======

MyQueue is a frontend for SLURM_/PBS_/LSF_ that makes handling of tasks easy.
It has a command-line interface called *mq* with a number of commands
and a Python interface for managing workflows.  Simple to set up: no
system administrator or database required.

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
* Chat: https://camd.zulipchat.com/ (#myqueue stream)


.. _SLURM: https://slurm.schedmd.com/
.. _PBS: https://en.m.wikipedia.org/wiki/Portable_Batch_System
.. _LSF: https://en.m.wikipedia.org/wiki/Platform_LSF


Examples
--------

Submit Python script to 32 cores for 2 hours::

    $ mq submit script.py -R 32:2h

Check results of tasks in current folder and its sub-folders::

    $ mq list  # or mq ls
    id  folder name      res.   age     state   time    error
    --- ------ --------- ------ ------- ------- ------- ------
    117 ./     script.py 32:10h 5:22:16 TIMEOUT 2:00:03
    ...
    ...
    --- ------ --------- ------ ------- ------- ------- ------
    TIMEOUT: 1, total: 5

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

MyQueue has only one dependency: Python_ version 3.6 or later.

Install MyQueue from PyPI_ with *pip*::

    $ python3 -m pip install myqueue --user

Enable bash tab-completion for future terminal sessions like this::

    $ mq completion >> ~/.profile

Run the tests::

    $ mq test

and report any errors you get on our `issue tracker`_.
Now, configure your system as described
`here <https://myqueue.readthedocs.io/en/latest/configuration.html>`__.


.. _Python: https://python.org/
.. _PyPI: https://pypi.org/project/myqueue/


Release notes
=============

See the `release notes`_ for a history of notable changes to MyQueue.

.. _release notes:: https://myqueue.readthedocs.io/en/latest/releasenotes.html


Help, support and feedback
==========================

If you need help, want to report a bug or suggest a new feature then you are
very welcome to get in touch via MyQueue's `issue tracker`_
or the *#myqueue* stream on Zulip_.

.. _issue tracker: https://gitlab.com/myqueue/myqueue/issues/
.. _Zulip: https://camd.zulipchat.com/


Contributing
============

We welcome contributions to the code and documentation, preferably as
merge-requests here: https://gitlab.com/myqueue/myqueue/merge_requests/.
