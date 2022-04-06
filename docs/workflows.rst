.. _workflows:

=========
Workflows
=========

The :ref:`workflow <workflow>` subcommand combined with a :ref:`workflow
script` can be used to run sequences of tasks in several folders.  The
script describes the tasks, their requirements and dependencies.

Example from real life:

* `Workflow for C2DB project
  <https://cmr.fysik.dtu.dk/c2db/c2db.html#workflow>`__


Simple example
==============

We want to factor some integers into primes.  We want to do two tasks: factor
the integer and check if the number was a prime number.

:download:`prime/factor.py`:

.. literalinclude:: prime/factor.py

:download:`prime/check.py`:

.. literalinclude:: prime/check.py

Our :ref:`workflow script` will create two tasks using the
:func:`myqueue.workflow.run` function and the :func:`myqueue.workflow.resources`
decorator.

:download:`prime/workflow.py`:

.. literalinclude:: prime/workflow.py

.. highlight:: bash

We put the three Python files in a ``prime/`` folder::

    $ ls -l prime/
    total 12
    -rw-rw-r-- 1 jensj jensj 190 Apr  6 11:24 check.py
    -rw-rw-r-- 1 jensj jensj 398 Apr  6 11:24 factor.py
    -rw-rw-r-- 1 jensj jensj 164 Apr  6 11:24 workflow.py

Make sure Python can find the files by adding this line::

    export PYTHONPATH=~/path/to/prime/:$PYTHONPATH

to your ``~/.bash_profile`` file.

Create some folders::

    $ mkdir numbers
    $ cd numbers
    $ mkdir 99 1001 8069 36791 98769 100007

and start the workflow in one of the folders::

    $ mq workflow ../prime/workflow.py 1001/ --dry-run
    Scanning folders: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1/1
    Submitting tasks: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2/2
    1 ./1001/ prime.factor    1:2s
    1 ./1001/ prime.check  d1 1:2s
    2 tasks to submit
    $ mq workflow ../prime/workflow.py 1001/
    Scanning folders: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1/1
    Submitting tasks: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2/2
    1 ./1001/ prime.factor    1:2s
    2 ./1001/ prime.check  d1 1:2s
    2 tasks submitted
    $ sleep 2

and now in all subfolders::

    $ mq ls
    id folder  name         res.  age state time
    ── ─────── ──────────── ──── ──── ───── ────
    1  ./1001/ prime.factor 1:2s 0:02 done  0:00
    2  ./1001/ prime.check  1:2s 0:02 done  0:00
    ── ─────── ──────────── ──── ──── ───── ────
    done: 2, total: 2
    $ mq workflow ../prime/workflow.py */
    Scanning folders: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6/6
    done: 2
    Submitting tasks: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 10/10
    3  ./100007/ prime.factor    1:2s
    4  ./36791/  prime.factor    1:2s
    5  ./8069/   prime.factor    1:2s
    6  ./98769/  prime.factor    1:2s
    7  ./99/     prime.factor    1:2s
    8  ./100007/ prime.check  d1 1:2s
    9  ./36791/  prime.check  d1 1:2s
    10 ./8069/   prime.check  d1 1:2s
    11 ./98769/  prime.check  d1 1:2s
    12 ./99/     prime.check  d1 1:2s
    10 tasks submitted

::

    $ sleep 2  # wait for tasks to finish
    $ mq ls
    id folder    name         res.  age state time
    ── ───────── ──────────── ──── ──── ───── ────
    1  ./1001/   prime.factor 1:2s 0:04 done  0:00
    2  ./1001/   prime.check  1:2s 0:04 done  0:00
    3  ./100007/ prime.factor 1:2s 0:02 done  0:00
    4  ./36791/  prime.factor 1:2s 0:02 done  0:00
    5  ./8069/   prime.factor 1:2s 0:02 done  0:00
    6  ./98769/  prime.factor 1:2s 0:02 done  0:00
    7  ./99/     prime.factor 1:2s 0:02 done  0:00
    8  ./100007/ prime.check  1:2s 0:02 done  0:00
    9  ./36791/  prime.check  1:2s 0:02 done  0:00
    10 ./8069/   prime.check  1:2s 0:02 done  0:00
    11 ./98769/  prime.check  1:2s 0:02 done  0:00
    12 ./99/     prime.check  1:2s 0:02 done  0:00
    ── ───────── ──────────── ──── ──── ───── ────
    done: 12, total: 12

Note that ``prime.check.done`` and ``prime.factor.done`` files are created
to mark that these tasks have been completed::

    $ ls -l 1001/
    total 12
    -rw-rw-r-- 1 jensj jensj 24 Apr  6 11:24 factors.json
    -rw-rw-r-- 1 jensj jensj  0 Apr  6 11:24 prime.check.2.err
    -rw-rw-r-- 1 jensj jensj  0 Apr  6 11:24 prime.check.2.out
    -rw-rw-r-- 1 jensj jensj 18 Apr  6 11:25 prime.check.state
    -rw-rw-r-- 1 jensj jensj  0 Apr  6 11:24 prime.factor.1.err
    -rw-rw-r-- 1 jensj jensj  0 Apr  6 11:24 prime.factor.1.out
    -rw-rw-r-- 1 jensj jensj 18 Apr  6 11:25 prime.factor.state

Now, add another number::

    $ mkdir 42
    $ mq workflow ../prime/workflow.py */
    Scanning folders: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 7/7
    done: 12
    Submitting tasks: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2/2
    13 ./42/ prime.factor    1:2s
    14 ./42/ prime.check  d1 1:2s
    2 tasks submitted

Turns out, there were two prime numbers::

    $ sleep 2
    $ grep factors */factors.json
    100007/factors.json:{"factors": [97, 1031]}
    1001/factors.json:{"factors": [7, 11, 13]}
    36791/factors.json:{"factors": [36791]}
    42/factors.json:{"factors": [2, 3, 7]}
    8069/factors.json:{"factors": [8069]}
    98769/factors.json:{"factors": [3, 11, 41, 73]}
    99/factors.json:{"factors": [3, 3, 11]}
    $ ls */PRIME
    36791/PRIME
    8069/PRIME
    $ mq rm -sd */ -q


Handling many tasks
-------------------

In the case where you have a workflow script with many tasks combined with
many folders, it can happen that ``mq workflow ... */`` will try to submit
more tasks than allowed by the scheduler.  In that case, you will have to
submit the tasks in batches::

    $ mq workflow ../prime/workflow.py */ --max-tasks=2000
    Scanning folders: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1500/1500
    Submitting tasks: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 2000/2000
    ...
    $ # wait ten days ...
    $ mq workflow ../prime/workflow.py */ --max-tasks=2000
    Scanning folders: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1500/1500
    done: 2000
    Submitting tasks: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1000/1000
    ...


.. _workflow script:

Workflow script
===============

A workflow script must contain a function:

.. function:: workflow() -> None

.. highlight:: python

The :func:`workflow` function should call the :func:`myqueue.workflow.run`
function for each task in the workflow.  Here is an example (``flow.py``)::

    from myqueue.workflow import run
    from somewhere import postprocess

    def workflow():
        r1 = run(script='task1.py')
        r2 = run(script='task2.py', cores=8, tmax='2h')
        run(function=postprocess, deps=[r1, r2])

where ``task1.py`` and ``task2.py`` are Python scripts and ``postprocess`` is
a Python function.  Calling the :func:`workflow` function directly will run
the ``task1.py`` script, then the ``task2.py`` script and finally the
``postprocess`` function.  If instead, the :func:`workflow` function  is
passed to the ``mq workflow flow.py`` command, then the :func:`run`
function will not actually run the tasks, but instead collect them with
dependencies and submit them.

Here is an alternative way to specify the dependencies of the ``postprocess``
step (see more :ref:`below <dependencies>`)::

    def workflow():
        r1 = run(script='task1.py')
        r2 = run(script='task2.py', cores=8, tmax='2h')
        with r1, r2:
            run(function=postprocess)

.. autofunction:: myqueue.workflow.run
.. autoclass:: myqueue.workflow.RunHandle
    :members:


Resources
---------

Resources for a task are set using the keywords:
``cores``, ``tmax``, ``processes``, ``nodename`` and ``repeats``.

.. seealso::

    :ref:`resources`.

Here are three equivalent ways to set the ``cores`` resource::

    def workflow():
        run(..., cores=24)  # as an argument to run()

    def workflow():
        with resources(cores=24):  # via a context manager
            run(...)

    @resources(cores=24)  # with a decorator
    def workflow():
        run(...)

.. autofunction:: myqueue.workflow.resources


Functions
---------

A task that call a Python function will make sure the function caches its
result. If the function ``f`` has an attribute ``has`` that is a callable
that can be called like ``f.has(*args, **kwargs)`` then MyQueue will use that
to check if the function has been called with a given set of arguments.  If a
function doesn't have a ``has`` attribute then MyQueue will wrap it in a
function that does using the :class:`~myqueue.caching.CachedFunction`
object.

.. autoclass:: myqueue.caching.CachedFunction
    :members:

Helper wrapper for working with functions:

.. autofunction:: myqueue.workflow.wrap

.. _dependencies:

Dependencies
------------

Suppose we have two tasks and we want ``<task-2>`` to start after ``<task-1>``.
We can specify the dependency explicitly like this::

    def workflow():
        run1 = run(<task-1>)
        run(<task-2>, deps=[run1])

or like this using a context manager::

    def workflow():
        with run(<task-1>):
            run(<task-2>)

If our tasks are functions then MyQueue can figure out the dependencies
without specifying them explicitly or using `with` statements.
Say we have the following two functions::

    def f1():
        return 2 + 2

    def f2(x):
        print(x)

and we want to call ``f2`` with the result of ``f1``.  Given this
workflow script::

    def workflow():
        run1 = run(function=f1)
        run(function=f2, args=[run1.result])

MyQueue will know that the ``f2`` task depends on the ``f1`` task.
Here is a shorter version using the :func:`~myqueue.workflow.wrap`
function::

    def workflow():
        x = wrap(f1)()
        wrap(f2)(x)


Workflows with if-statements
============================

Some workflows may take different directions depending on the result of the
first part of the workflow.  Continuing with out ``f1`` and ``f2`` functions,
we may only want to call ``f2`` if the result of ``f1`` is lees than five::

    def workflow():
        run1 = run(function=f1)
        if run1.result < 5:
            run(function=f2, args=[run1.result])

MyQueue will know that ``run1.result < 5`` can't be decided before the first
task has been run and it will therfore only submit one task. Running ``mq
workflow ...`` a second time after the first task has finished will submit
the second task.  Here is an equivalent script using functions::

    def workflow():
        x = wrap(f1)()
        if x < 5:
            wrap(f2)(x)

The :class:`~myqueue.workflow.RunHandle` object also has a ``done`` attribute
that can be used to break up the workflow::

    def workflow():
        run1 = run(<task-1>)
        if run1.done:
            something = read_result_of_task1_from file()
            if ... something ...:
                run(<task-2>)


Old workflow script
===================

.. warning::

    Please use a new-style :ref:`workflow script`!


Old-style workflow scripts contain a function:

.. function:: create_tasks() -> List[myqueue.task.Task]

.. highlight:: python

It should return a list of :class:`myqueue.task.Task` objects created with the
:func:`myqueue.task.task` helper function.  Here is an example::

    from myqueue.task import task
    def create_tasks():
        t1 = task('<task-1>', resources=...)
        t2 = task('<task-2>', resources=...)
        t3 = task('<task-3>', resources=...,
                  deps=['<task-1>', '<task-2>'])
        return [t1, t2, t3]

where ``<task-n>`` is the name of a task.  See :ref:`task examples` below.


.. _task examples:

Examples
--------

.. seealso::

    :ref:`tasks` and :ref:`resources`.

Two equivalent ways to set the resources::

    task('prime.factor', resources='8:1h')
    task('prime.factor', cores=8, tmax='1h')

Given these two tasks::

    t1 = task('mod@f1')
    t2 = task('mod@f2')

here are three equivalent ways to set dependencies::

    t3 = task('mod@f3', deps=[t1, t2])
    t3 = task('mod@f3', deps=['mod@f1', 'mod@f2'])
    t3 = task('mod@f3', deps='mod@f1,mod@f2')

Arguments in three equivalent ways::

    task('math@sin+3.14')
    task('math@sin', args=[3.14])
    task('math@sin', args=['3.14'])

More than one argument::

    task('math@gcd+42_117')
    task('math@gcd', args=[42, 117]')

same as:

>>> import math
>>> math.gcd(42, 117)
3
