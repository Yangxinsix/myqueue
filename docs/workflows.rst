.. _workflows:

=========
Workflows
=========

The :ref:`workflow <workflow>` subcommand combined with a :ref:`workflow
script` can be used to run several similar tasks in several folders.  The
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
:func:`myqueue.task.task` function.

:download:`prime/workflow.py`:

.. literalinclude:: prime/workflow.py

.. highlight:: bash

We put the three Python files in a ``prime/`` folder::

    $ ls -l prime/
    totalt 12
    -rw-rw-r-- 1 jensj jensj 190 feb  3 14:07 check.py
    -rw-rw-r-- 1 jensj jensj 387 feb  3 14:07 factor.py
    -rw-rw-r-- 1 jensj jensj 164 feb  3 14:07 workflow.py

Make sure Python can find the files by adding this line::

    export PYTHONPATH=~/path/to/prime/:$PYTHONPATH

to your ``~/.bash_profile`` file.

Create some folders::

    $ mkdir numbers
    $ cd numbers
    $ mkdir 99 1001 8069 36791 98769 100007

and start the workflow in one of the folders::

    $ mq workflow ../prime/workflow.py 1001/ --dry-run
    Scanning 1 folder: |--------------------| 100.0%
    ./1001/ prime.factor    1:2s
    ./1001/ prime.check  d1 1:2s
    2 tasks to submit
    $ mq workflow ../prime/workflow.py 1001/
    Scanning 1 folder: |--------------------| 100.0%
    Submitting 2 tasks: |--------------------| 100.0%
    1 ./1001/ prime.factor    1:2s
    2 ./1001/ prime.check  d1 1:2s
    2 tasks submitted
    $ sleep 2

and now in all subfolders::

    $ mq ls
    id folder  name         res.  age state time
    -- ------- ------------ ---- ---- ----- ----
    1  ./1001/ prime.factor 1:2s 0:02 done  0:00
    2  ./1001/ prime.check  1:2s 0:02 done  0:00
    -- ------- ------------ ---- ---- ----- ----
    done: 2, total: 2
    $ mq workflow ../prime/workflow.py */
    Scanning 6 folders: |--------------------| 100.0%
    2 tasks already done
    Submitting 10 tasks: |--------------------| 100.0%
    3  ./100007/ prime.factor    1:2s
    4  ./100007/ prime.check  d1 1:2s
    5  ./36791/  prime.factor    1:2s
    6  ./36791/  prime.check  d1 1:2s
    7  ./8069/   prime.factor    1:2s
    8  ./8069/   prime.check  d1 1:2s
    9  ./98769/  prime.factor    1:2s
    10 ./98769/  prime.check  d1 1:2s
    11 ./99/     prime.factor    1:2s
    12 ./99/     prime.check  d1 1:2s
    10 tasks submitted

::

    $ sleep 2  # wait for tasks to finish
    $ mq ls
    id folder    name         res.  age state time
    -- --------- ------------ ---- ---- ----- ----
    1  ./1001/   prime.factor 1:2s 0:04 done  0:00
    2  ./1001/   prime.check  1:2s 0:04 done  0:00
    3  ./100007/ prime.factor 1:2s 0:02 done  0:00
    4  ./100007/ prime.check  1:2s 0:02 done  0:00
    5  ./36791/  prime.factor 1:2s 0:02 done  0:00
    6  ./36791/  prime.check  1:2s 0:02 done  0:00
    7  ./8069/   prime.factor 1:2s 0:02 done  0:00
    8  ./8069/   prime.check  1:2s 0:02 done  0:00
    9  ./98769/  prime.factor 1:2s 0:02 done  0:00
    10 ./98769/  prime.check  1:2s 0:02 done  0:00
    11 ./99/     prime.factor 1:2s 0:02 done  0:00
    12 ./99/     prime.check  1:2s 0:02 done  0:00
    -- --------- ------------ ---- ---- ----- ----
    done: 12, total: 12

Note that ``prime.check.done`` and ``prime.factor.done`` files are created
to mark that these tasks has been completed::

    $ ls -l 1001/
    totalt 4
    -rw-rw-r-- 1 jensj jensj 24 feb  3 14:07 factors.json
    -rw-rw-r-- 1 jensj jensj  0 feb  3 14:07 prime.check.2.err
    -rw-rw-r-- 1 jensj jensj  0 feb  3 14:07 prime.check.2.out
    -rw-rw-r-- 1 jensj jensj  0 feb  3 14:07 prime.check.done
    -rw-rw-r-- 1 jensj jensj  0 feb  3 14:07 prime.factor.1.err
    -rw-rw-r-- 1 jensj jensj  0 feb  3 14:07 prime.factor.1.out
    -rw-rw-r-- 1 jensj jensj  0 feb  3 14:07 prime.factor.done

Now, add another number::

    $ mkdir 42
    $ mq workflow ../prime/workflow.py */
    Scanning 7 folders: |--------------------| 100.0%
    12 tasks already done
    Submitting 2 tasks: |--------------------| 100.0%
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
    Scanning 1500 folders: |--------------------| 100.0%
    ...
    Submitting 2000 tasks: |--------------------| 100.0%
    $ # wait ten days ...
    $ mq workflow ../prime/workflow.py */ --max-tasks=2000
    ...
    2000 tasks already done
    Submitting 1000 tasks: |--------------------| 100.0%


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
passed to the the ``mq workflow flow.py`` command, then the :func:`run`
function will not actually run the tasks, but instead collect them with
dependencies and submit them.

Here is an alternative way to specify the dependencies of the ``postprocess``
step::

    def workflow():
        r1 = run(script='task1.py')
        r2 = run(script='task2.py', cores=8, tmax='2h')
        with r1, r2:
            run(function=postprocess)

.. autofunction:: myqueue.workflow.run


Resources
---------

.. seealso::

    :ref:`resources`.

Three equivalent ways to set the resources::

    def workflow():
        run(..., cores=24)  # as an argument to run()

    @resources(cores=24)  # with a decorator
    def workflow():
        run(...)

    def workflow():
        @resources(cores=24):  # via a context manager
            run(...)

.. autofunction:: myqueue.workflow.resources


Functions
---------

.. autofunction:: myqueue.workflow.wrap



Old workflow script
===================

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
