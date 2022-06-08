.. _releases:

=============
Release notes
=============

.. highlight:: bash

Next release
============

* ...


Version 22.6.0
==============

* Fixed bug related to several users having write access to the same
  ``.myqueue/`` folder.


Version 22.3.0
==============

* There is now one background daemon per user.  This will allow several users
  to share a ``.myqueue/`` folder.


Version 22.1.0
==============

* The :ref:`list` command can now list several folders instead of,
  as previously, only one.
  They must all belong to the same ``.myqueue/`` folder though.


Version 21.8.0
==============

* The simple "local" scheduler is now feature complete.
  See :ref:`scheduler`.

* The `mpi_implementations` configuration option is no longer needed and has
  been deprecated.

* MyQueue no longer tries to keep track of all your ``.myqueue/`` folders.
  Consequently, the ``--all`` option has been removed from the :ref:`list
  <list>`, :ref:`kick <kick>` and :ref:`sync <sync>` commands.

* There is a new ``mq info --all [folder]`` command that will searsch for
  your ``.myqueue/`` folders and print a status line for each.

* There is now one background daemon per ``.myqueue/`` folder.  See
  :ref:`daemon process`.


Version 21.7.0
==============

* Email notifications: ``mq modify ... -N dA``.  See :ref:`modify` and
  :ref:`notifications`.
* You can now use ``mq info`` to get information about your MyQueue
  installation:

  * version
  * location of the source code
  * location of ``.myqueue/`` folder
  * configuration


Version 21.4.2
==============

* Make things work with Python 3.7.


Version 21.4.1
==============

* Backwards compatibility fix.


Version 21.4.0
==============

* For workflow tasks, ``name.done`` and ``name.FAILED`` files have now been
  replaced by a ``name.state`` file.  MyQueue will still read the old files,
  but no longer write them.


Version 21.2.0
==============

* PRELIMINARY: New way to specify workflows using :func:`myqueue.workflow.run`,
  :func:`myqueue.workflow.wrap` and :func:`myqueue.workflow.resources`.
  See :ref:`workflow script`.


Version 21.1.0
==============

* New :ref:`config command <config>` for guessing your configuration.
  See :ref:`autoconfig`.
* LSF-backend fixes.


Version 20.11.3
===============

* Bugfix: LSF-backend fixes.


Version 20.11.2
===============

* Bugfix: Don't remove FAILED-files in dry-run mode.


Version 20.11.1
===============

* Fix "workflow target" bug and ``MQ:`` comments bug.


Version 20.11.0
===============

* New ``mq workflow ... --arguments "key=val,..."`` option.  See
  :ref:`workflow`.
* Two new columns in :ref:`list output <list>`: *arguments* and *info*.
  Can be hidden with: ``mq ls -c aI-``.
* Deprecated ``venv/activate`` script.  Use ``venv/bin/activate`` instead.
  See :ref:`venv`.
* Resources can now be specified in the scripts as special comments::

      # MQ: resources=24:2h


Version 20.9.1
==============

* Fix workflow+openmpi issue.


Version 20.9.0
==============

* Red error messages.
* Progress-bar.


Version 20.5.0
==============

* Using pytest_ for testing.
* Simple *local* queue for use without a real scheduler.
* New ``extra_args`` configuration parameter (:ref:`extra_args`).
  Replaces, now deprecated, ``features`` and ``reservation`` parameters.
* Use ``python3 -m myqueue.config`` to auto-configure your system.
* Memory usage is now logged.

.. _pytest: https://docs.pytest.org/en/latest/


Version 20.1.2
==============

* Bug-fix release with fix for single-process tasks (see :ref:`resources`).


Version 20.1.1
==============

* This is the version submitted to JOSS.


Version 20.1.0
==============

* New shortcuts introduced for specifying :ref:`states`: ``a`` is ``qhrd``
  and ``A`` is ``FCMT``.


Version 19.11.1
===============

* New command: :ref:`daemon`.


Version 19.11.0
===============

* Small bugfixes and improvements.


Version 19.10.1
===============

* Added support for LSF scheduler.

* Added ``--max-tasks`` option for *submit* and *workflow* commands.


Version 19.10.0
===============

* Shell-style wildcard matching of task names and error messages
  is now possible::

    $ mq ls -n "*abc-??.py"
    $ mq resubmit -s F -e "*ZeroDivision*"

* Three new :ref:`cli` options: ``mq -V/--version``, ``mq ls --not-recursive``
  and ``mq submit/workflow -f/--force``.

* All task-events (queued, running, stopped) are now logged to
  ``~/.myqueue/log.csv``.  List tasks from log-file with::

    $ mq ls -L ...


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
