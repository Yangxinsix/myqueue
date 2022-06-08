.. _cli:

======================
Command-line interface
======================

.. _commands:

Sub-commands
============

.. computer generated text:

.. list-table::
    :widths: 1 3

    * - :ref:`help <help>`
      - Show how to use this tool
    * - :ref:`list <list>` (ls)
      - List tasks in queue
    * - :ref:`submit <submit>`
      - Submit task(s) to queue
    * - :ref:`resubmit <resubmit>`
      - Resubmit failed or timed-out tasks
    * - :ref:`remove <remove>` (rm)
      - Remove or cancel task(s)
    * - :ref:`info <info>`
      - Show detailed information about MyQueue or a task
    * - :ref:`workflow <workflow>`
      - Submit tasks from Python script or several scripts matching pattern
    * - :ref:`run <run>`
      - Run task(s) on local computer
    * - :ref:`kick <kick>`
      - Restart T and M tasks (timed-out and out-of-memory)
    * - :ref:`modify <modify>`
      - Modify task(s)
    * - :ref:`init <init>`
      - Initialize new queue
    * - :ref:`sync <sync>`
      - Make sure SLURM/LSF/PBS and MyQueue are in sync
    * - :ref:`completion <completion>`
      - Set up tab-completion for Bash
    * - :ref:`config <config>`
      - Create config.py file
    * - :ref:`daemon <daemon>`
      - Interact with the background process


.. _help:

Help: Show how to use this tool
-------------------------------

usage: mq help [-h] [cmd]

Show how to use this tool.

More help can be found here: https://myqueue.readthedocs.io/.

cmd:
    Subcommand.

options:
  -h, --help  show this help message and exit


.. _list:

List (ls): List tasks in queue
------------------------------

usage: mq list [-h] [-s qhrdFCTMaA] [-i ID] [-n NAME] [-e ERROR]
               [-c ifnaIrAste] [-S c] [-C] [-L] [--not-recursive] [-v] [-q]
               [-T]
               [folder ...]

List tasks in queue.

Only tasks in the chosen folder and its subfolders are shown.

Columns::

    i: id
    f: folder
    n: name of task
    a: arguments
    I: info: "+<nargs>,*<repeats>,d<ndeps>"
    r: resources
    A: age
    s: state
    t: time
    e: error message

Examples::

    $ mq list -s rq  # show running and queued jobs
    $ mq ls -s F abc/  # show failed jobs in abc/ folder

folder:
    List tasks in this folder and its subfolders. Defaults to current folder. Use --not-recursive to exclude subfolders.

options:
  -h, --help            show this help message and exit
  -s qhrdFCTMaA, --states qhrdFCTMaA
                        Selection of states. First letters of "queued",
                        "hold", "running", "done", "FAILED", "CANCELED",
                        "TIMEOUT", "MEMORY", "all" and "ALL".
  -i ID, --id ID        Comma-separated list of task ID's. Use "-i -" for
                        reading ID's from stdin (one ID per line; extra stuff
                        after the ID will be ignored).
  -n NAME, --name NAME  Select only tasks with names matching "NAME" (* and ?
                        can be used).
  -e ERROR, --error ERROR
                        Select only tasks with error message matching "ERROR"
                        (* and ? can be used).
  -c ifnaIrAste, --columns ifnaIrAste
                        Select columns to show. Use "-c a-" to remove the "a"
                        column.
  -S c, --sort c        Sort rows using column c, where c must be one of i, f,
                        n, a, r, A, s, t or e. Use "-S c-" for a descending
                        sort.
  -C, --count           Just show the number of tasks.
  -L, --use-log-file    List tasks from logfile (~/.myqueue/log.csv).
  --not-recursive       Do not list subfolders.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


.. _submit:

Submit: Submit task(s) to queue
-------------------------------

usage: mq submit [-h] [-d DEPENDENCIES] [-n NAME] [--restart N] [-f]
                 [--max-tasks MAX_TASKS] [-R RESOURCES] [-w] [-z] [-v] [-q]
                 [-T]
                 task [folder ...]

Submit task(s) to queue.

Example::

    $ mq submit script.py -R 24:1d  # 24 cores for 1 day

task:
    Task to submit.
folder:
    Submit tasks in this folder. Defaults to current folder.

options:
  -h, --help            show this help message and exit
  -d DEPENDENCIES, --dependencies DEPENDENCIES
                        Comma-separated task names.
  -n NAME, --name NAME  Name used for task.
  --restart N           Restart N times if task times out or runs out of
                        memory. Time-limit will be doubled for a timed out
                        task and number of cores will be increased to the next
                        number of nodes for a task that runs out of memory.
  -f, --force           Submit also failed tasks.
  --max-tasks MAX_TASKS
                        Maximum number of tasks to submit.
  -R RESOURCES, --resources RESOURCES
                        Examples: "8:1h", 8 cores for 1 hour. Use "m" for
                        minutes, "h" for hours and "d" for days. "16:1:30m":
                        16 cores, 1 process, half an hour. "1:xeon40:5m": 1
                        core on "xeon40" for 5 minutes.
  -w, --workflow        Write <task-name>.state file when task has finished.
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


.. _resubmit:

Resubmit: Resubmit failed or timed-out tasks
--------------------------------------------

usage: mq resubmit [-h] [-R RESOURCES] [-w] [-s qhrdFCTMaA] [-i ID] [-n NAME]
                   [-e ERROR] [-z] [-v] [-q] [-T] [-r]
                   [folder ...]

Resubmit failed or timed-out tasks.

Example::

    $ mq resubmit -i 4321  # resubmit job with id=4321

folder:
    Task-folder. Use --recursive (or -r) to include subfolders.

options:
  -h, --help            show this help message and exit
  -R RESOURCES, --resources RESOURCES
                        Examples: "8:1h", 8 cores for 1 hour. Use "m" for
                        minutes, "h" for hours and "d" for days. "16:1:30m":
                        16 cores, 1 process, half an hour. "1:xeon40:5m": 1
                        core on "xeon40" for 5 minutes.
  -w, --workflow        Write <task-name>.state file when task has finished.
  -s qhrdFCTMaA, --states qhrdFCTMaA
                        Selection of states. First letters of "queued",
                        "hold", "running", "done", "FAILED", "CANCELED",
                        "TIMEOUT", "MEMORY", "all" and "ALL".
  -i ID, --id ID        Comma-separated list of task ID's. Use "-i -" for
                        reading ID's from stdin (one ID per line; extra stuff
                        after the ID will be ignored).
  -n NAME, --name NAME  Select only tasks with names matching "NAME" (* and ?
                        can be used).
  -e ERROR, --error ERROR
                        Select only tasks with error message matching "ERROR"
                        (* and ? can be used).
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.
  -r, --recursive       Use also subfolders.


.. _remove:

Remove (rm): Remove or cancel task(s)
-------------------------------------

usage: mq remove [-h] [-s qhrdFCTMaA] [-i ID] [-n NAME] [-e ERROR] [-z] [-v]
                 [-q] [-T] [-r]
                 [folder ...]

Remove or cancel task(s).

Examples::

    $ mq remove -i 4321,4322  # remove jobs with ids 4321 and 4322
    $ mq rm -s d . -r  # remove done jobs in this folder and its subfolders

folder:
    Task-folder. Use --recursive (or -r) to include subfolders.

options:
  -h, --help            show this help message and exit
  -s qhrdFCTMaA, --states qhrdFCTMaA
                        Selection of states. First letters of "queued",
                        "hold", "running", "done", "FAILED", "CANCELED",
                        "TIMEOUT", "MEMORY", "all" and "ALL".
  -i ID, --id ID        Comma-separated list of task ID's. Use "-i -" for
                        reading ID's from stdin (one ID per line; extra stuff
                        after the ID will be ignored).
  -n NAME, --name NAME  Select only tasks with names matching "NAME" (* and ?
                        can be used).
  -e ERROR, --error ERROR
                        Select only tasks with error message matching "ERROR"
                        (* and ? can be used).
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.
  -r, --recursive       Use also subfolders.


.. _info:

Info: Show detailed information about MyQueue or a task
-------------------------------------------------------

usage: mq info [-h] [-v] [-q] [-T] [-i ID] [-A] [folder]

Show detailed information about MyQueue or a task.

Example::

    $ mq info  # show information about MyQueue
    $ mq info 12345  # show information about task with id=12345

folder:
    Show information for queues in this folder and its subfolders. Defaults to current folder.

options:
  -h, --help       show this help message and exit
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.
  -i ID, --id ID   Show information about specific task.
  -A, --all        Show information about all your queues.


.. _workflow:

Workflow: Submit tasks from Python script or several scripts matching pattern
-----------------------------------------------------------------------------

usage: mq workflow [-h] [-f] [--max-tasks MAX_TASKS] [-t TARGETS] [-p]
                   [-a ARGUMENTS] [-z] [-v] [-q] [-T]
                   script [folder ...]

Submit tasks from Python script or several scripts matching pattern.

The script(s) must define a workflow() function as shown here::

    $ cat flow.py
    from myqueue.workflow import run
    def workflow():
        with run(<task1>):
            run(<task2>)
    $ mq workflow flow.py F1/ F2/  # submit tasks in F1 and F2 folders

script:
    Submit tasks from workflow script.
folder:
    Submit tasks in this folder. Defaults to current folder.

options:
  -h, --help            show this help message and exit
  -f, --force           Submit also failed tasks.
  --max-tasks MAX_TASKS
                        Maximum number of tasks to submit.
  -t TARGETS, --targets TARGETS
                        Comma-separated target names. Without any targets, all
                        tasks will be submitted.
  -p, --pattern         Use submit scripts matching "script" pattern in all
                        subfolders.
  -a ARGUMENTS, --arguments ARGUMENTS
                        Pass arguments to workflow() function. Example: "-a
                        name=hello,n=5" will call workflow(name='hello', n=5).
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


.. _run:

Run: Run task(s) on local computer
----------------------------------

usage: mq run [-h] [-n NAME] [-w] [-z] [-v] [-q] [-T] task [folder ...]

Run task(s) on local computer.

Remove task(s) from queue and run locally.

Example::

    $ mq run script.py f1/ f2/

task:
    Task to run locally.
folder:
    Submit tasks in this folder. Defaults to current folder.

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  Name used for task.
  -w, --workflow        Write <task-name>.state file when task has finished.
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


.. _kick:

Kick: Restart T and M tasks (timed-out and out-of-memory)
---------------------------------------------------------

usage: mq kick [-h] [-z] [-v] [-q] [-T] [folder]

Restart T and M tasks (timed-out and out-of-memory).

The queue is kicked automatically every ten minutes - so you don't have to do
it manually.

folder:
    Kick tasks in this folder and its subfolders. Defaults to current folder.

options:
  -h, --help       show this help message and exit
  -z, --dry-run    Show what will happen without doing anything.
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


.. _modify:

Modify: Modify task(s)
----------------------

usage: mq modify [-h] [-E STATES] [-N NEW_STATE] [-s qhrdFCTMaA] [-i ID]
                 [-n NAME] [-e ERROR] [-z] [-v] [-q] [-T] [-r]
                 [folder ...]

Modify task(s).

The following state changes are allowed: h->q, q->h, F->M and F->T.

folder:
    Task-folder. Use --recursive (or -r) to include subfolders.

options:
  -h, --help            show this help message and exit
  -E STATES, --email STATES
                        Send email when state changes to one of the specified
                        states (one or more of the letters: rdFCTMA).
  -N NEW_STATE, --new-state NEW_STATE
                        New state (one of the letters: qhrdFCTM).
  -s qhrdFCTMaA, --states qhrdFCTMaA
                        Selection of states. First letters of "queued",
                        "hold", "running", "done", "FAILED", "CANCELED",
                        "TIMEOUT", "MEMORY", "all" and "ALL".
  -i ID, --id ID        Comma-separated list of task ID's. Use "-i -" for
                        reading ID's from stdin (one ID per line; extra stuff
                        after the ID will be ignored).
  -n NAME, --name NAME  Select only tasks with names matching "NAME" (* and ?
                        can be used).
  -e ERROR, --error ERROR
                        Select only tasks with error message matching "ERROR"
                        (* and ? can be used).
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.
  -r, --recursive       Use also subfolders.


.. _init:

Init: Initialize new queue
--------------------------

usage: mq init [-h] [-z] [-v] [-q] [-T]

Initialize new queue.

This will create a .myqueue/ folder in your current working directory and copy
~/.myqueue/config.py into it.

options:
  -h, --help       show this help message and exit
  -z, --dry-run    Show what will happen without doing anything.
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


.. _sync:

Sync: Make sure SLURM/LSF/PBS and MyQueue are in sync
-----------------------------------------------------

usage: mq sync [-h] [-z] [-v] [-q] [-T] [folder]

Make sure SLURM/LSF/PBS and MyQueue are in sync.

Remove tasks that SLURM/LSF/PBS doesn't know about.  Also removes a task if
its corresponding folder no longer exists.

folder:
    Sync tasks in this folder and its subfolders. Defaults to current folder.

options:
  -h, --help       show this help message and exit
  -z, --dry-run    Show what will happen without doing anything.
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


.. _completion:

Completion: Set up tab-completion for Bash
------------------------------------------

usage: mq completion [-h] [-v] [-q] [-T]

Set up tab-completion for Bash.

Do this::

    $ mq completion >> ~/.bashrc

options:
  -h, --help       show this help message and exit
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


.. _config:

Config: Create config.py file
-----------------------------

usage: mq config [-h] [-Q QUEUE_NAME] [--in-place] [-z] [-v] [-q] [-T]
                 [{local,slurm,pbs,lsf}]

Create config.py file.

This tool will try to guess your configuration.  Some hand editing afterwards
will most likely be needed. Read more about config.py file here::

    https://myqueue.readthedocs.io/en/latest/configuration.html

Example::

    $ mq config -Q hpc lsf

{local,slurm,pbs,lsf}:
     Name of scheduler. Will be guessed if not supplied.

options:
  -h, --help            show this help message and exit
  -Q QUEUE_NAME, --queue-name QUEUE_NAME
                        Name of queue. May be needed.
  --in-place            Overwrite ~/.myqueue/config.py file.
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


.. _daemon:

Daemon: Interact with the background process
--------------------------------------------

usage: mq daemon [-h] [-z] [-v] [-q] [-T] {start,stop,status} [folder]

Interact with the background process.

Manage daemon for sending notifications, restarting, holding and releasing
tasks.

{start,stop,status}:
    Start, stop or check status.
folder:
    Pick daemon process corresponding to this folder. Defaults to current folder.

options:
  -h, --help           show this help message and exit
  -z, --dry-run        Show what will happen without doing anything.
  -v, --verbose        More output.
  -q, --quiet          Less output.
  -T, --traceback      Show full traceback.
