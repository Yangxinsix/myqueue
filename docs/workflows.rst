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
    -rw-r--r-- 1 jensj jensj 170 Jan 22 12:56 check.py
    -rw-rw-r-- 1 jensj jensj 361 Jan 22 12:53 factor.py
    -rw-r--r-- 1 jensj jensj 140 Jan 22 13:32 workflow.py

and add that folder to ``$PYTHONPATH`` so that Python can find the files::

    $ echo "export PYTHONPATH=$PWD:$PYTHONPATH" >> ~/.bash_profile

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
    1 ./1001/ prime.factor 1:10m*
    2 ./1001/ prime.check  1:10m(1)*
    2 tasks submitted

and now in all subfolders::

    $ mq workflow ../prime/workflow.py */
    2 tasks already in the queue:
        done    : 1
        running : 1
    3  ./100007/ prime.factor 1:10m*
    4  ./100007/ prime.check  1:10m(1)*
    5  ./36791/  prime.factor 1:10m*
    6  ./36791/  prime.check  1:10m(1)*
    7  ./8069/   prime.factor 1:10m*
    8  ./8069/   prime.check  1:10m(1)*
    9  ./98769/  prime.factor 1:10m*
    10 ./98769/  prime.check  1:10m(1)*
    11 ./99/     prime.factor 1:10m*
    12 ./99/     prime.check  1:10m(1)*
    10 tasks submitted
    $ mq ls
    id folder    name         res.       age state  time error
    -- --------- ------------ --------- ---- ------ ---- -----
    1  ./1001/   prime.factor 1:10m*    0:00 done   0:00
    2  ./1001/   prime.check  1:10m*    0:00 done   0:00
    3  ./100007/ prime.factor 1:10m*    0:00 done   0:00
    4  ./100007/ prime.check  1:10m*    0:00 queued 0:00
    5  ./36791/  prime.factor 1:10m*    0:00 queued 0:00
    6  ./36791/  prime.check  1:10m(1)* 0:00 queued 0:00
    7  ./8069/   prime.factor 1:10m*    0:00 queued 0:00
    8  ./8069/   prime.check  1:10m(1)* 0:00 queued 0:00
    9  ./98769/  prime.factor 1:10m*    0:00 queued 0:00
    10 ./98769/  prime.check  1:10m(1)* 0:00 queued 0:00
    11 ./99/     prime.factor 1:10m*    0:00 queued 0:00
    12 ./99/     prime.check  1:10m(1)* 0:00 queued 0:00
    -- --------- ------------ --------- ---- ------ ---- -----
    done: 3, queued: 9, total: 12

::

    $ sleep 2  # wait for tasks to finish
    $ mq ls
    id folder    name         res.    age state time error
    -- --------- ------------ ------ ---- ----- ---- -----
    1  ./1001/   prime.factor 1:10m* 0:02 done  0:00
    2  ./1001/   prime.check  1:10m* 0:02 done  0:00
    3  ./100007/ prime.factor 1:10m* 0:02 done  0:00
    4  ./100007/ prime.check  1:10m* 0:02 done  0:00
    5  ./36791/  prime.factor 1:10m* 0:01 done  0:00
    6  ./36791/  prime.check  1:10m* 0:01 done  0:00
    7  ./8069/   prime.factor 1:10m* 0:01 done  0:00
    8  ./8069/   prime.check  1:10m* 0:01 done  0:00
    9  ./98769/  prime.factor 1:10m* 0:01 done  0:00
    10 ./98769/  prime.check  1:10m* 0:01 done  0:00
    11 ./99/     prime.factor 1:10m* 0:01 done  0:00
    12 ./99/     prime.check  1:10m* 0:01 done  0:00
    -- --------- ------------ ------ ---- ----- ---- -----
    done: 12, total: 12

Note that a ``prime.check.done`` file is created to mark that the ``prime.check`` task is done.   and the when a task has been
completed::

    $ ls -l 1001/
    total 4
    -rw-r--r-- 1 jensj jensj 24 Jan 22 14:56 factors.json
    -rw-r--r-- 1 jensj jensj  0 Jan 22 14:56 prime.check.2.err
    -rw-r--r-- 1 jensj jensj  0 Jan 22 14:56 prime.check.2.out
    -rw-r--r-- 1 jensj jensj  0 Jan 22 14:56 prime.check.done
    -rw-r--r-- 1 jensj jensj  0 Jan 22 14:56 prime.factor.1.err
    -rw-r--r-- 1 jensj jensj  0 Jan 22 14:56 prime.factor.1.out
    -rw-r--r-- 1 jensj jensj  0 Jan 22 14:56 prime.factor.done

Now, add another number::

    $ mkdir 42
    $ mq workflow ../prime/workflow.py */
    12 tasks already marked as done ("<task-name>.done" file exists)
    13 ./42/ prime.factor 1:10m*
    14 ./42/ prime.check  1:10m(1)*
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

Three equivalent ways to set the resources::

    task('prime.factor@8:1h')
    task('prime.factor', resources='8:1h')
    task('prime.factor', cores=8, tmax='1h')

Given these two tasks::

    t1 = task('mod:f1')
    t2 = task('mod:f2')

here are three equivalent ways to set dependencies::

    t3 = task('mod:f3', deps=[t1, t2])
    t3 = task('mod:f3', deps=['mod:f1', 'mod:f2'])
    t3 = task('mod:f3', deps='mod:f1,mod:f2')

Arguments::

    task('math:sin+3.14')
    task('math:sin+3.14@1:10m')
    task('math:sin', args=[3.14])
    task('math:sin', args=['3.14'])
