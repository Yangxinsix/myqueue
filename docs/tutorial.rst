========
Tutorial
========

Tasks
=====

A task can be one of these:

* a Python script (``script.py``)
* a Python module (``module``)
* a function in a Python module (``module:function``)
* an executable or shell-script


States
======

These are the possible states a task can be in:

* queued
* hold
* running
* done
* FAILED
* CANCELED
* MEMORY
* TIMEOUT

Abbreviations: q, h, r, d, F, C, M and T.


Examples
========

Run ``script.py`` on 8 cores for 10 hours in ``folder1`` and ``folder2``::

    $ mq submit script.py@8:10h folder1/ folder2/

Sleep for 25 seconds on 1 core using the ``time.sleep()`` function::

    $ mq submit time:sleep -a 25 -R 1:1m

or equivalently::

    $ mq submit time:sleep+25@1:1m

Say "hello" (using the defaults of 1 core for 10 minutes)::

    $ mq submit echo -a hello

You can see the status of your jobs with::

    $ mq list
    id folder name       res.   age state time error
    -- ------ ---------- ----- ---- ----- ---- -----
    1  ~      echo+hello 1:10m 0:06 done  0:00
    -- ------ ---------- ----- ---- ----- ---- -----
    done: 1

Remove the job from the list with::

    $ mq remove -s d .

The output from the job will be in ``~/echo+hello.1.out`` and
``~/echo+hello.1.err`` (if there was any output).

::

    $ cat echo+hello.1.out
    hello

If a job fails or times out, then you can resubmit it with more resources::

    $ mq submit sleep+3000@1:30m
    ...
    $ mq list
    id folder name       res.   age state   time  error
    -- ------ ---------- ----- ---- ------- ----- -----
    2  ~      sleep+3000 1:30m 1:16 TIMEOUT 50:00
    -- ------ ---------- ----- ---- ------- ----- -----
    TIMEOUT: 1
    $ mq resubmit -i 2 -R 1:1h


Resources
=========

A resource specification has the form::

    cores[:nodename][:processes]:tmax

Examples:

* ``1:1h`` 1 core and 1 process for 1 hour
* ``64:xeon:2d`` 64 cores and 64 processes on "xeon" nodes for 2 days
* ``24:1:30m`` 24 cores and 1 process for 30 minutes
