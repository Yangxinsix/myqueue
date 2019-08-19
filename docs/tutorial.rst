========
Tutorial
========

.. _tasks:

Tasks
=====

A task can be one of these:

* a Python script: ``script.py``
* a Python module: ``module``
* a Python submodule: ``module.submodule``
* a function in a Python module: ``module@function``
* a shell command (from ``$PATH``): ``shell:command``
* a shell-script: ``./script``


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

* Sleep for 2 seconds on 1 core using the :func:`time.sleep()` Python
  function::

    $ mq submit "time@sleep 2" -R 1:1m

* Run the ``echo hello`` shell command in two folders
  (using the defaults of 1 core for 10 minutes)::

    $ mkdir f1 f2
    $ mq submit "shell:echo hello" f1/ f2/

* Run ``script.py`` on 8 cores for 10 hours::

    $ echo "x = 1 / 0" > script.py
    $ mq submit script.py -R 8:10h

You can see the status of your jobs with::

    $ mq list
    id folder name             res.   age state time error
    -- ------ ---------------- ----- ---- ----- ---- -----
    1  ~      shell:echo+hello 1:10m 0:06 done  0:00
    -- ------ ---------------- ----- ---- ----- ---- -----
    done: 1

Remove the failed and done jobs from the list with::

    $ mq remove -s Fd .

The output from files from a task will look like this::

    $ ls -l f2
    $ cat f2/shell:echo+hello.3.out
    hello

If a job fails or times out, then you can resubmit it with more resources::

    $ mq submit "shell:sleep 4" -R 1:2s
    ...
    $ mq list
    id folder name             res.   age state   time  error
    -- ------ ---------------- ----- ---- ------- ----- -----
    2  ~      shell:sleep+3000 1:30m 1:16 TIMEOUT 50:00
    -- ------ ---------------- ----- ---- ------- ----- -----
    TIMEOUT: 1
    $ mq resubmit -i 5 -R 1:1m


.. _resources:

Resources
=========

A resource specification has the form::

    cores[:nodename][:processes]:tmax

Examples:

* ``1:1h`` 1 core and 1 process for 1 hour
* ``64:xeon:2d`` 64 cores and 64 processes on "xeon" nodes for 2 days
* ``24:1:30m`` 24 cores and 1 process for 30 minutes
