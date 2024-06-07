.. _releases:

=============
Release notes
=============

(version numbers can be interpreted as ``year.month.bug-fix-release-number``)

.. highlight:: bash

Next release
============

* ...


Version 24.5.1
==============

* Fixed a problem with multinode jobs with 1 process
  (:issue:`58`, :mr:`144`).


Version 24.5.0
==============

* SLURM jobs will now be submitted with ``--cpus-per-task`` set to the correct
  value.
* The ``MYQUEUE_TASK_ID`` environment variable will now be set to
  the task ID so that running tasks can inspect it.
* New configuration variable for :ref:`serial_python`.


Version 24.1.0
==============

* Drop support for Python 3.7.
* Move from ``setup.py`` to ``pyproject.toml``.
* The :ref:`resubmit <resubmit>` command will now remove the old task.
  Use ``--keep`` to get the old behavior.
* Restarted (OOM'ed or timed out) tasks will now be cleared from the queue.
* Improved parsing or ``.err`` files.


Version 23.4.0
==============

* Fixed broken tab-completion for names and ids: ``mq ls -i <tab>``
  (:mr:`132`).
* Failed dependencies would block *everthing* in a workflow.  Should be
  fixed in :mr:`135`.


Version 23.1.0
==============

* Fixed a problem with dependencies inside subfolders (:issue:`51`).


Version 22.12.0
===============

* Added ``--extra-scheduler-args`` option to :ref:`submit <submit>`
  and :ref:`resubmit <resubmit>` commands.

* Added ``special`` flag to node description.

* Make sure old daemons from older versions stop running (:mr:`130`).


Version 22.11.3
===============

* Fixed dependency bug (:mr:`128`).


Version 22.11.2
===============

* Fix :issue:`48` and other regressions after move to :mod:`sqlite3`.


Version 22.11.1
===============

* Add missing ``weight`` argument to :func:`myqueue.workflow.run`.


Version 22.11.0
===============

.. important::

   No more ``<task-name>.state`` files.  MyQueue will only know the state
   af a task if it is listed in your queue.  There are two exceptions to
   this rule:

   1) If a task is set to create some files like here::

        def workflow():
            run(..., creates=['file1.abc', 'file2.xyz'], ...)

      then MyQueue will consider the task done if those files exist.
      See :func:`myqueue.workflow.run`.

   2) If a task is a Python function like here::

        def workflow():
            run(function=func, args=[...], name='abc', ...)

      then MyQueue will consider the task done if the result file exists
      (in this case ``abc.result``).  See
      :class:`myqueue.caching.json_cached_function`.

* Your queue is no longer stored in a ``.myqueue/queue.json`` file.  Instead,
  it is now in a :mod:`sqlite3` file in ``.myqueue/queue.sqlite3``.
  Your old JSON file will automatically be migrated to the new format.

* Removed the *mq run* command (it may return later: :issue:`44`).

* Calling a Python function from a workflow (``run(function=...)``)
  will now write the return value to a file called ``<task-name>.result``
  in the JSON format.  Previously the return value was written to the
  ``.state`` file.

* Removing tasks part of a workflow now needs a ``--force``
  (as MyQueue will no longer know the states of such tasks).

* Most commands have been sped up by delaying import of ``rich``
  and ``networkx``.

* The :ref:`resubmit <resubmit>` command will no longer remove the old task.
  Use ``--remove`` to get the old behavior.

* The :ref:`resources` of a task now includes a *task-weight*.  This can be
  used to limit the number of running tasks.  See more here:
  :ref:`task_weight`.


Version 22.9.0
==============

* Hitting CTRL-C in the middle of submitting jobs is now safe.


Version 22.7.1
==============

* Fixed: :issue:`mq list does not work with ID specifier (-i) <42>`.


Version 22.7.0
==============

* Tasks will no longer activate a virtual environment if a ``venv/`` folder
  is found in one of the parent folders.
* Tasks submitted from an activated virtual environment will now activate that
  environment when the job starts running.
* Better error message when ``sbatch``/``qsub``/``bsub`` fails.
* Improved parsing of ``stderr`` from failed jobs.
* Depth first submit ordering.  A workflow with an ``A`` task and a ``B``
  task where ``B`` depends on ``A`` would previously run all the ``A``
  tasks and then all the ``B`` tasks.  The order will now be ``A``, ``B``
  in the first folder, then  ``A``, ``B`` in the next folder and so on.


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
