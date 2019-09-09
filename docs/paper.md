---
title: 'MyQueue: Task and workflow management for humans'
tags:
  - Python
  - ...
authors:
  - name: Jens Jørgen Mortensen
    orcid: 0000-0003-0872-7098
    affiliation: 1
  - name: Morten Gjerding
    orcid: 0000-0002-5256-660X
    affiliation: 1
affiliations:
 - name: DTU
   index: 1
date: 11 November 2019
bibliography: paper.bib
---

# Summary

``MyQueue`` is a frontend for ``SLURM`` and ``PBS`` that makes handling of
tasks easy [@slurm][@pbs]. It has a command-line interface called *mq* with a
number of sub-commands and a Python interface for managing workflows.

The idea behind ``MyQueue`` is that you have your own queue that you can
*submit* tasks to and ``MyQueue`` will handle interactions with your
scheduler (``SLURM`` or ``PBS``).  Once tasks have finished, they will stay
in your queue so that you can *list* them and see the status (done, failed,
timed out or out of memory). Tasks will stay in your queue until you
explicitly *remove* them.  This makes it easy to keep track of your tasks:
If a task is listed as "done" then this will remind you that you need to do
something with the result.  If a task failed then you need to fix something
and *resubmit* the task.  In this way, ``MyQueue`` works as a to-do list.

The *list* sub-command is very powerful.  It will by default only show tasks
belonging to the current folder and its sub-folders making it easy to manage
several projects by putting them in separate folders.  You can select the
tasks you want to list by status or name and failed tasks will show the error
message.  A task can be marked with a *restarts* number indicating that
``MyQueue`` should restart the task (with increased resources) that number of
times if it runs out of time or memory.

``MyQueue`` has a Python interface that can be used to define workflows.
Here, one defines a dependency tree of tasks that ``MyQueue`` can use to
submit tasks. It is based on folders and files which makes it very easy to
get started - no system administrator or central database server is needed.
This workflow has been used successfully to drive several high-throughput
screening studies coordinating on the order of 100,000 individual tasks
[@c2db], [@c3db], [@asr], [@felix].

# Acknowledgements

We acknowledge contributions from ..., and support ... during the genesis of
this project.

# References

