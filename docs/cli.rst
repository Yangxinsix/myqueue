======================
Command-line interface
======================

Commands
========

.. computer generated text:

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
