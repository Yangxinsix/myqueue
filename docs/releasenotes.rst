.. _releases:

=============
Release notes
=============


Next release
============

* Shell-style wildcard matching of task names and error messages
  is now possible::

    $ mq ls -n "*abc-??.py"
    $ mq resubmit -s F -e "*ZeroDivision*"

* Two new :ref:`cli` options: ``--verbose`` and ``--force``.

* All task-events (queued, running, stopped) are now logged to
  ``~/.myqueue/log.csv``.



Version 19.9.0
==============

* New ``-C`` option for the :ref:`mq ls <list>` command for showing only the
  count of tasks in the queue::

    $ mq ls -C
    running: 12, queued: 3, FAILED: 1, total: 16

* A background process will now automatically :ref:`kick <kick>`
  your queues every ten minutes.

* Project moved to a new *myqueue* group: https://gitlab.com/myqueue/myqueue/


Version 19.8.0
==============

* The ``module:function`` syntax has been changed to ``module@function``.
* Arguments to tasks are now specified like this::

    $ mq submit [options] "<task> arg1 arg2 ..." [folder1 [folder2 ...]]

* New ``run`` command::

    $ mq run [options] "<task> arg1 arg2 ..." [folder1 [folder2 ...]]


Version 19.6.0
==============

* Tasks will now activate a virtual environment if a ``venv/`` folder is found
  in one of the parent folders.  The activation script will be ``venv/activate``
  or ``venv/bin/activate`` if ``venv/activate`` does not exist.


Version 19.5.0
==============

* New ``--target`` option for :ref:`workflows <workflows>`.
* New API's for submitting jobs: :meth:`myqueue.task.Task.submit` and
  :func:`myqueue.submit`.
* New ``--name`` option for the :ref:`submit <submit>` command.
* No more ``--arguments`` option.  Use::

    $ mq submit [options] <task> [folder1 [folder2 ...]] -- arg1 arg2 ...


Version 19.2.0
==============

* Fix test-suite.


Version 19.1.0
==============

* Recognizes mpiexex variant automatically.

* New "detailed information" subcommand.


Version 18.12.0
===============

* The ``restart`` parameter is now an integer (number of restarts) that
  counts down to zero.  Avoids infinite loop.


Version 0.1.0
=============

Initial release.
