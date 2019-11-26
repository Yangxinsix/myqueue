.. _workflows:

=========
Workflows
=========

The :ref:`workflow <workflow>` subcommand combined with a :ref:`workflow
script` can be used to run several similar tasks in several folders.  The
script describes the tasks, their requirements and dependencies.


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
    total 12
    -rw-r--r-- 1 jensj jensj 190 Oct 28 11:12 check.py
    -rw-r--r-- 1 jensj jensj 387 Oct 28 11:12 factor.py
    -rw-r--r-- 1 jensj jensj 166 Oct 28 11:12 workflow.py

Make sure Python can find the files by adding this line::

    export PYTHONPATH=~/path/to/prime/:$PYTHONPATH

to your ``~/.bash_profile`` file.

Create some folders::

    $ mkdir numbers
    $ cd numbers
    $ mkdir 99 1001 8069 36791 98769 100007

and start the workflow in one of the folders::

    $ mq workflow ../prime/workflow.py 1001/ --dry-run
    ./1001/ prime.factor 1:10m*
    ./1001/ prime.check  1:10m(1)*
    2 tasks to submit
    $ mq workflow ../prime/workflow.py 1001/
    14 ./1001/ prime.factor 1:10m*
    15 ./1001/ prime.check  1:10m(1)*
    2 tasks submitted
    $ sleep 2

and now in all subfolders::

    $ mq ls
    id folder  name         res.    age state time error
    -- ------- ------------ ------ ---- ----- ---- -----
    14 ./1001/ prime.factor 1:10m* 0:03 done  0:00
    15 ./1001/ prime.check  1:10m* 0:03 done  0:00
    -- ------- ------------ ------ ---- ----- ---- -----
    done: 2, total: 2
    $ mq workflow ../prime/workflow.py */
    2 tasks already done
    16 ./100007/ prime.factor 1:10m*
    17 ./100007/ prime.check  1:10m(1)*
    18 ./36791/  prime.factor 1:10m*
    19 ./36791/  prime.check  1:10m(1)*
    20 ./8069/   prime.factor 1:10m*
    21 ./8069/   prime.check  1:10m(1)*
    22 ./98769/  prime.factor 1:10m*
    23 ./98769/  prime.check  1:10m(1)*
    24 ./99/     prime.factor 1:10m*
    25 ./99/     prime.check  1:10m(1)*
    10 tasks submitted

::

    $ sleep 2  # wait for tasks to finish
    $ mq ls
    id folder    name         res.    age state time error
    -- --------- ------------ ------ ---- ----- ---- -----
    14 ./1001/   prime.factor 1:10m* 0:08 done  0:00
    15 ./1001/   prime.check  1:10m* 0:08 done  0:00
    16 ./100007/ prime.factor 1:10m* 0:04 done  0:00
    17 ./100007/ prime.check  1:10m* 0:04 done  0:00
    18 ./36791/  prime.factor 1:10m* 0:04 done  0:00
    19 ./36791/  prime.check  1:10m* 0:04 done  0:00
    20 ./8069/   prime.factor 1:10m* 0:04 done  0:00
    21 ./8069/   prime.check  1:10m* 0:04 done  0:00
    22 ./98769/  prime.factor 1:10m* 0:04 done  0:00
    23 ./98769/  prime.check  1:10m* 0:04 done  0:00
    24 ./99/     prime.factor 1:10m* 0:04 done  0:00
    25 ./99/     prime.check  1:10m* 0:04 done  0:00
    -- --------- ------------ ------ ---- ----- ---- -----
    done: 12, total: 12

Note that a ``prime.check.done`` file is created to mark that the
``prime.check`` task has been completed::

    $ ls -l 1001/
    total 4
    -rw-r--r-- 1 jensj jensj 24 Oct 28 11:12 factors.json
    -rw-r--r-- 1 jensj jensj  0 Oct 28 11:12 prime.check.15.err
    -rw-r--r-- 1 jensj jensj  0 Oct 28 11:12 prime.check.15.out
    -rw-r--r-- 1 jensj jensj  0 Oct 28 11:12 prime.check.done
    -rw-r--r-- 1 jensj jensj  0 Oct 28 11:12 prime.factor.14.err
    -rw-r--r-- 1 jensj jensj  0 Oct 28 11:12 prime.factor.14.out

There is no ``prime.factor.done`` file because ``factors.json`` serves that
purpose.

Now, add another number::

    $ mkdir 42
    $ mq workflow ../prime/workflow.py */
    12 tasks already done
    26 ./42/ prime.factor 1:10m*
    27 ./42/ prime.check  1:10m(1)*
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


Handling very many tasks
------------------------

In the case where you have a workflow script with many tasks combined with
many folders, it can happen that ``mq workflow ... */`` will try to submit
more tasks than allowed by the scheduler.  In that case, you will have to
submit the tasks in batches::

    $ mq workflow ../prime/workflow.py */ --max-tasks=4000
    ...
    4000 tasks submitted
    $ # wait ten days ...
    $ mq workflow ../prime/workflow.py */ --max-tasks=4000
    4000 tasks already done
    ...
    3178 tasks submitted


.. _workflow script:

Workflow script
===============

A workflow script must contain a function:

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
