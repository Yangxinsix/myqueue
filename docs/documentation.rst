=============
Documentation
=============

.. _tasks:

Tasks
=====

A task can be one of these:

* a Python module:

  Examples:

  * ``module``
  * ``module.submodule`` (a Python submodule)

* a function in a Python module:

      ``module@function``

* a Python script:

  Examples:

  * ``script.py`` (use ``script.py`` in folders where tasks are running)
  * ``./script.py`` (use ``script.py`` from folder where tasks were submitted)
  * ``/path/to/script.py`` (absolute path)

* a shell command:

      ``shell:command`` (``command`` must be in ``$PATH``)

* a shell-script:

      ``./script``


States
======

These are the 8 possible states a task can be in:


======  ========  =======  =======
queued  hold      running  done
FAILED  CANCELED  MEMORY   TIMEOUT
======  ========  =======  =======

Abbreviations: ``q``, ``h``, ``r``, ``d``, ``F``, ``C``, ``M`` and ``T``.


.. _resources:

Resources
=========

A resource specification has the form::

    cores[:nodename][:processes]:tmax

Examples:

* ``1:1h`` 1 core and 1 process for 1 hour
* ``64:xeon:2d`` 64 cores and 64 processes on "xeon" nodes for 2 days
* ``24:1:30m`` 24 cores and 1 process for 30 minutes


.. highlight:: bash

Examples
========

* Sleep for 2 seconds on 1 core using the :func:`time.sleep()` Python
  function::

    $ mq submit "time@sleep 2" -R 1:1m
    1 ./ time@sleep+2 1:1m
    1 task submitted

* Run the ``echo hello`` shell command in two folders
  (using the defaults of 1 core for 10 minutes)::

    $ mkdir f1 f2
    $ mq submit "shell:echo hello" f1/ f2/
    2 ./f1/ shell:echo+hello 1:10m
    3 ./f2/ shell:echo+hello 1:10m
    2 tasks submitted

* Run ``script.py`` on 8 cores for 10 hours::

    $ echo "x = 1 / 0" > script.py
    $ mq submit script.py -R 8:10h
    4 ./ script.py 8:10h
    1 task submitted

You can see the status of your jobs with::

    $ mq list
    id folder name             res.   age state  time error
    -- ------ ---------------- ----- ---- ------ ---- -----------------------------------
    1  ./     time@sleep+2     1:1m  0:04 done   0:02
    2  ./f1/  shell:echo+hello 1:10m 0:01 done   0:00
    3  ./f2/  shell:echo+hello 1:10m 0:01 done   0:00
    4  ./     script.py        8:10h 0:00 FAILED 0:00 ZeroDivisionError: division by zero
    -- ------ ---------------- ----- ---- ------ ---- -----------------------------------
    done: 3, FAILED: 1, total: 4

Remove the failed and done jobs from the list with
(notice the dot meaning the current folder)::

    $ mq remove -s Fd -r .
    1 ./    time@sleep+2     1:1m  0:04 done   0:02
    2 ./f1/ shell:echo+hello 1:10m 0:01 done   0:00
    3 ./f2/ shell:echo+hello 1:10m 0:01 done   0:00
    4 ./    script.py        8:10h 0:00 FAILED 0:00 ZeroDivisionError: division by zero
    4 tasks removed

The output files from a task will look like this::

    $ ls -l f2
    total 4
    -rw-r--r-- 1 jensj jensj 0 Aug 19 14:57 shell:echo+hello.3.err
    -rw-r--r-- 1 jensj jensj 6 Aug 19 14:57 shell:echo+hello.3.out
    $ cat f2/shell:echo+hello.3.out
    hello

If a job fails or times out, then you can resubmit it with more resources::

    $ mq submit "shell:sleep 4" -R 1:2s
    5 ./ shell:sleep+4 1:10m
    1 task submitted
    $ mq list
    id folder name          res.  age state   time error
    -- ------ ------------- ---- ---- ------- ---- -----
    5  ./     shell:sleep+4 1:10m 0:02 TIMEOUT 0:02
    -- ------ ------------- ---- ---- ------- ---- -----
    TIMEOUT: 1, total: 1
    $ mq resubmit -i 5 -R 1:1m
    6 ./ shell:sleep+4 1:1m
    1 task submitted
