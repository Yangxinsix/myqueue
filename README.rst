.. image:: https://gitlab.com/myqueue/myqueue/badges/master/coverage.svg
.. image:: https://badge.fury.io/py/myqueue.svg
    :target: https://badge.fury.io/py/myqueue

.. contents::

=======
MyQueue
=======

MyQueue is a frontend for SLURM_/LSF_/PBS_ that makes handling of tasks easy.
It has a command-line interface called ``mq`` with a number of *commands*
and a Python interface for managing *workflows*.  Simple to set up: no
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

    * Folder-based *Workflows*

Quick links:

* Documentation: https://myqueue.readthedocs.io/
* Code: https://gitlab.com/myqueue/myqueue/
* Issues: https://gitlab.com/myqueue/myqueue/issues/
* Chat: https://camd.zulipchat.com/ (#myqueue)


.. _SLURM: https://slurm.schedmd.com/
.. _PBS: https://en.m.wikipedia.org/wiki/Portable_Batch_System
.. _LSF: https://en.m.wikipedia.org/wiki/Platform_LSF


Examples
--------

Submit Python script to 32 cores and 2 hours::

    $ mq submit script.py -R 32:2h

Check results of tasks in current folder and its sub-folders::

    $ mq list  # or mq ls
    id folder name      res.   age     state   time    error
    -- ------ --------- ------ ------- ------- ------- ------
    117 ./    script.py 32:10h 5:22:16 TIMEOUT 2:00:03
    -- ------ --------- ------ ------- ------- ------- ------
    TIMEOUT: 1, total: 1

Resubmit with more resources::

     $ mq resubmit -i 117 -R 32:1d

See all *commands* here_ and XXXX


Installation
============

Dependencies:

* Python_ (>= 3.6)

Install MyQueue from PyPI_ with ``pip``::

    $ python3 -m pip install myqueue --user

Enable bash tab-completion for future terminal sessions like this::

    $ mq completion >> ~/.profile

Run the tests::

    $ mq test

and report any errors you get: https://gitlab.com/myqueue/myqueue/issues/.


.. _Python: https://python.org/
.. _PyPI: https://pypi.org/project/myqueue/


Changelog
=========

See the changelog_ for a history of notable changes to MyQueue.

.. _changelog:: https://myqueue.readthedocs.io/en/latest/releasenotes.html


Help, support and feedback
==========================

If you need help, want to report a bug or suggest a new feature then you are
very welcome to get in touch via MyQueue's `issue tracker`_
 or the `#myqueue` stream on Zulip_.

.. _issue tracker:: https://gitlab.com/myqueue/myqueue/issues/
.. _Zulip:: https://camd.zulipchat.com/


Contributing
============

We welcome contributions to the code and documentation, preferably as merge-
requests here: https://gitlab.com/myqueue/myqueue/merge_requests/.
