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
    * - :ref:`workflow <workflow>`
      - Submit tasks from script
    * - :ref:`kick <kick>`
      - Restart T and M tasks (timed-out and out-of-memory)
    * - :ref:`completion <completion>`
      - Set up tab-completion for Bash
    * - :ref:`test <test>`
      - Run tests
    * - :ref:`modify <modify>`
      - Modify task(s)
    * - :ref:`init <init>`
      - Initialize new queue
    * - :ref:`info <info>`
      - Show detailed information about task
    * - :ref:`sync <sync>`
      - Make sure SLURM/PBS and MyQueue are in sync


.. _help:

Help: Show how to use this tool
-------------------------------

usage: mq help [-h] [cmd]

Show how to use this tool.

More help can be found here: https://myqueue.readthedocs.io/.

cmd:
    Subcommand.

optional arguments:
  -h, --help  show this help message and exit


.. _list:

List (ls): List tasks in queue
------------------------------

usage: mq list [-h] [-s qhrdFCTM] [-i ID] [-n NAME] [-c ifnraste] [-S c] [-v]
               [-q] [-T] [-A]
               [folder]

List tasks in queue.

Only tasks in the chosen folder and its subfolders are shown.

Examples::

    $ mq list -s rq  # show running and queued jobs
    $ mq ls -s F abc/  # show failed jobs in abc/ folder

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
  -S c, --sort c        Sort rows using column c, where c must be one of i, f,
                        n, r, a, s, t or e. Use "-S c-" for a descending sort.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.
  -A, --all             List all myqueue folders (from ~/.myqueue/folders.txt)


.. _submit:

Submit: Submit task(s) to queue
-------------------------------

usage: mq submit [-h] [-d DEPENDENCIES] [-n NAME] [--restart N] [-R RESOURCES]
                 [-w] [-z] [-v] [-q] [-T]
                 task [folder [folder ...]]
                 [-- arg [arg ...]]

Submit task(s) to queue.

Example::

    $ mq submit script.py -R 24:1d  # 24 cores for 1 day

task:
    Task to submit.
folder:
    Submit tasks in this folder. Defaults to current folder.

optional arguments:
  -h, --help            show this help message and exit
  -d DEPENDENCIES, --dependencies DEPENDENCIES
                        Comma-separated task names.
  -n NAME, --name NAME  Name used for task.
  --restart N           Restart N times if task times out or runs out of
                        memory. Time-limit will be doubled for a timed out
                        task and number of cores will be increased to the next
                        number of nodes for a task that runs out of memory.
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


.. _resubmit:

Resubmit: Resubmit failed or timed-out tasks
--------------------------------------------

usage: mq resubmit [-h] [-R RESOURCES] [-w] [-s qhrdFCTM] [-i ID] [-n NAME]
                   [-z] [-v] [-q] [-T] [-r]
                   [folder [folder ...]]

Resubmit failed or timed-out tasks.

Example::

    $ mq resubmit -i 4321  # resubmit job with id=4321

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


.. _remove:

Remove (rm): Remove or cancel task(s)
-------------------------------------

usage: mq remove [-h] [-s qhrdFCTM] [-i ID] [-n NAME] [-z] [-v] [-q] [-T] [-r]
                 [folder [folder ...]]

Remove or cancel task(s).

Examples::

    $ mq remove -i 4321,4322  # remove jobs with ids 4321 and 4322
    $ mq rm -s d . -r  # remove done jobs in this folder and its subfolders

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


.. _workflow:

Workflow: Submit tasks from script
----------------------------------

usage: mq workflow [-h] [-t TARGETS] [-p] [-z] [-v] [-q] [-T]
                   script [folder [folder ...]]

Submit tasks from script.

The script can be a simple Python script or a Python module. If script/module
contains a create_tasks() function then create tasks defined in this function.
Otherwise look for "dependencies" and "resources" variables in script and
create workflow tree from these variables. Example of script containing
"create_tasks()"::

    $ cat flow.py
    from myqueue.task import task
    def create_tasks():
        return [task('task1'),
                task('task2', deps='task1')]
    $ mq workflow flow.py F1/ F2/  # submit tasks in F1 and F2 folders

Myqueue can also deduce a workflow from a script itself by looking for the
resources and dependencies variables. For example, to tell myqueue that script
"a.py" depends on "b.py" then "a.py" must contain::

    $ cat a.py
    ...
    dependencies = ['b.py']
    ...

Similarly, resources can be given by specifying "resources = '8:10h'" which
would give 8 cores for 10 hours.

script:
    Workflow submit script or module. If module, then create workflow from module dependencies
folder:
    Submit tasks in this folder. Defaults to current folder.

optional arguments:
  -h, --help            show this help message and exit
  -t TARGETS, --targets TARGETS
                        Comma-separated target names. Without any targets, all
                        tasks will be submitted.
  -p, --pattern         Use submit scripts matching "pattern" in all
                        subfolders.
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


.. _kick:

Kick: Restart T and M tasks (timed-out and out-of-memory)
---------------------------------------------------------

usage: mq kick [-h] [-z] [-v] [-q] [-T] [-A] [--install-crontab-job] [folder]

Restart T and M tasks (timed-out and out-of-memory).

You can kick the queue manually with "mq kick" or automatically by adding that
command to a crontab job (can be done with "mq kick --install-crontab-job").

folder:
    Kick tasks in this folder and its subfolders. Defaults to current folder.

optional arguments:
  -h, --help            show this help message and exit
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.
  -A, --all             Kick all myqueue folders (from ~/.myqueue/folders.txt)
  --install-crontab-job
                        Install crontab job to kick your queues every half
                        hour.


.. _completion:

Completion: Set up tab-completion for Bash
------------------------------------------

usage: mq completion [-h] [-v] [-q] [-T]

Set up tab-completion for Bash.

Do this::

    $ mq completion >> ~/.bashrc

optional arguments:
  -h, --help       show this help message and exit
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


.. _test:

Test: Run tests
---------------

usage: mq test [-h] [--config-file CONFIG_FILE] [-x EXCLUDE] [-z] [-v] [-q]
               [-T]
               [test [test ...]]

Run tests.

Please report errors to https://gitlab.com/jensj/myqueue/issues.

test:
    Test to run. Default behaviour is to run all.

optional arguments:
  -h, --help            show this help message and exit
  --config-file CONFIG_FILE
                        Use specific config.py file.
  -x EXCLUDE, --exclude EXCLUDE
                        Exclude test(s).
  -z, --dry-run         Show what will happen without doing anything.
  -v, --verbose         More output.
  -q, --quiet           Less output.
  -T, --traceback       Show full traceback.


.. _modify:

Modify: Modify task(s)
----------------------

usage: mq modify [-h] [-s qhrdFCTM] [-i ID] [-n NAME] [-z] [-v] [-q] [-T] [-r]
                 newstate [folder [folder ...]]

Modify task(s).

The following state changes are allowed: h->q, q->h, F->M and F->T.

newstate:
    New state (one of the letters: qhrdFCTM).
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


.. _init:

Init: Initialize new queue
--------------------------

usage: mq init [-h] [-z] [-v] [-q] [-T]

Initialize new queue.

This will create a .myqueue/ folder in your current working directory and copy
~/.myqueue/config.py into it.

optional arguments:
  -h, --help       show this help message and exit
  -z, --dry-run    Show what will happen without doing anything.
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


.. _info:

Info: Show detailed information about task
------------------------------------------

usage: mq info [-h] [-z] [-v] [-q] [-T] id [folder]

Show detailed information about task.

id:
    Task ID.
folder:
    Show task from this folder. Defaults to current folder.

optional arguments:
  -h, --help       show this help message and exit
  -z, --dry-run    Show what will happen without doing anything.
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.


.. _sync:

Sync: Make sure SLURM/PBS and MyQueue are in sync
-------------------------------------------------

usage: mq sync [-h] [-z] [-v] [-q] [-T] [-A] [folder]

Make sure SLURM/PBS and MyQueue are in sync.

Remove tasks that SLURM/PBS doesn't know about.  Also removes a task if its
corresponding folder no longer exists.

folder:
    Sync tasks in this folder and its subfolders. Defaults to current folder.

optional arguments:
  -h, --help       show this help message and exit
  -z, --dry-run    Show what will happen without doing anything.
  -v, --verbose    More output.
  -q, --quiet      Less output.
  -T, --traceback  Show full traceback.
  -A, --all        Sync all myqueue folders (from ~/.myqueue/folders.txt)
