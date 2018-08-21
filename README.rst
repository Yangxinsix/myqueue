=======
MyQueue
=======

Simple frontend for SLURM_ and PBS_.

.. _SLURM: https://slurm.schedmd.com/
.. _PBS: http://www.pbspro.org/

.. contents::


Installation
============

Get the code and install with ``pip``::

    $ git clone https://gitlab.com/jensj/myqueue.git
    $ cd myqueue
    $ python3 -m pip install --user --editable .

Make sure ``~/.local/bin/`` is in your ``$PATH`` and enable bash tab-completion
like this::

    $ mq completion -q >> ~/.bashrc


Configuration
=============

You need to configure your SLURM/PBS system with a ~/.myqueue/config.py file.
The simplest way is to copy the file from a friend::

    $ ls ~/../*/.myqueue/config.py
    /home/you/../alice/.myqueue/config.py
    /home/you/../bob/.myqueue/config.py
    ...
    $ cp ~alice/.myqueue/config.py ~/.myqueue/config.py


Tasks
=====

A task can be one of these:

* a Python script (script.py)
* a Python module (module)
* a function in a Python module (module.function)
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

    $ mq submit time.sleep -a 25 -R 1:1m

or equivalently::

    $ mq submit time.sleep+25@1:1m

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


.. computer generated text:

Commands
========


List command
------------

usage: mq list [-h] [-s qhrdFCTM] [-i ID] [-n NAME] [-c ifnraste] [-v] [-q]
               [-T]
               [folder [folder ...]]

List tasks in queue.

folder:
    List tasks in this folder and its subfolders. Defaults to current folder.

optional arguments:
  -h, --help            show this help message and exit
  -s qhrdFCTM, --states qhrdFCTM
                        Selection of states. First letters of "queued",
                        "hold", "running", "done", "FAILED", "CANCELED" and
                        "TIMEOUT".
  -i ID, --id ID        Comma-separated list of task ID's. Use "-i -" for
                        reading ID's from stdin (one ID per line; extra stuff
                        after the ID will be ignored).
  -n NAME, --name NAME  Select only tasks named "NAME".
  -c ifnraste, --columns ifnraste
                        Select columns to show.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


Submit command
--------------

usage: mq submit [-h] [-d DEPENDENCIES] [-a ARGUMENTS] [--restart]
                 [-R RESOURCES] [-w] [-z] [-v] [-q] [-T]
                 task [folder [folder ...]]

Submit task(s) to queue.

task:
    Task to submit.
folder:
    Submit tasks in this folder. Defaults to current folder.

optional arguments:
  -h, --help            show this help message and exit
  -d DEPENDENCIES, --dependencies DEPENDENCIES
                        Comma-separated task names.
  -a ARGUMENTS, --arguments ARGUMENTS
                        Comma-separated arguments for task.
  --restart             Restart if task times out or runs out of memory. Time-
                        limit will be doubled for a timed out task and number
                        of cores will be doubled for a task that runs out of
                        memory.
  -R RESOURCES, --resources RESOURCES
                        Examples: "8:1h", 8 cores for 1 hour. Use "m" for
                        minutes, "h" for hours and "d" for days. "16:1:30m":
                        16 cores, 1 process, half an hour.
  -w, --workflow        Write <task-name>.done or <task-name>.FAILED file when
                        done.
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


Resubmit command
----------------

usage: mq resubmit [-h] [-R RESOURCES] [-w] [-s qhrdFCTM] [-i ID] [-n NAME]
                   [-z] [-v] [-q] [-T] [-r]
                   [folder [folder ...]]

Resubmit failed or timed-out tasks.

folder:
    Task-folder. Use --recursive (or -r) to include subfolders.

optional arguments:
  -h, --help            show this help message and exit
  -R RESOURCES, --resources RESOURCES
                        Examples: "8:1h", 8 cores for 1 hour. Use "m" for
                        minutes, "h" for hours and "d" for days. "16:1:30m":
                        16 cores, 1 process, half an hour.
  -w, --workflow        Write <task-name>.done or <task-name>.FAILED file when
                        done.
  -s qhrdFCTM, --states qhrdFCTM
                        Selection of states. First letters of "queued",
                        "hold", "running", "done", "FAILED", "CANCELED" and
                        "TIMEOUT".
  -i ID, --id ID        Comma-separated list of task ID's. Use "-i -" for
                        reading ID's from stdin (one ID per line; extra stuff
                        after the ID will be ignored).
  -n NAME, --name NAME  Select only tasks named "NAME".
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.
  -r, --recursive       Use also subfolders.


Remove command
--------------

usage: mq remove [-h] [-s qhrdFCTM] [-i ID] [-n NAME] [-z] [-v] [-q] [-T] [-r]
                 [folder [folder ...]]

Remove or cancel task(s).

folder:
    Task-folder. Use --recursive (or -r) to include subfolders.

optional arguments:
  -h, --help            show this help message and exit
  -s qhrdFCTM, --states qhrdFCTM
                        Selection of states. First letters of "queued",
                        "hold", "running", "done", "FAILED", "CANCELED" and
                        "TIMEOUT".
  -i ID, --id ID        Comma-separated list of task ID's. Use "-i -" for
                        reading ID's from stdin (one ID per line; extra stuff
                        after the ID will be ignored).
  -n NAME, --name NAME  Select only tasks named "NAME".
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.
  -r, --recursive       Use also subfolders.


Workflow command
----------------

usage: mq workflow [-h] [-p] [-z] [-v] [-q] [-T] script [folder [folder ...]]

Submit tasks from Python script.

script:
    Submit script.
folder:
    Submit tasks in this folder. Defaults to current folder.

optional arguments:
  -h, --help       show this help message and exit
  -p, --pattern    Use submit scripts matching "script" in all subfolders.
  -z, --dry-run    Show what will happen without doing anything.
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


Sync command
------------

usage: mq sync [-h] [-z] [-v] [-q] [-T]

Make sure SLURM/PBS and MyQueue are in sync.

optional arguments:
  -h, --help       show this help message and exit
  -z, --dry-run    Show what will happen without doing anything.
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


Completion command
------------------

usage: mq completion [-h] [-v] [-q] [-T]

Set up tab-completion.

optional arguments:
  -h, --help       show this help message and exit
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


Test command
------------

usage: mq test [-h] [--non-local] [-x EXCLUDE] [-z] [-v] [-q] [-T]
               [test [test ...]]

Run tests.

test:
    Test to run. Default behaviour is to run all.

optional arguments:
  -h, --help            show this help message and exit
  --non-local           Run tests using SLURM/PBS.
  -x EXCLUDE, --exclude EXCLUDE
                        Exclude test(s).
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.