---
title: 'MyQueue: Task and workflow scheduling system'
tags:
  - Python
  - ...
authors:
  - name: Jens Jørgen Mortensen
    orcid: 0000-0001-5090-6706
    affiliation: 1
  - name: Morten Gjerding
    orcid: 0000-0002-5256-660X
    affiliation: 1
  - name: Kristian Sommer Thygesen
    orcid: 0000-0001-5197-214X
    affiliation: 1
affiliations:
 - name: Technical University of Denmark
   index: 1
date: 11 November 2019
bibliography: paper.bib
---

# Summary

Task scheduling and workload management on high-performance computing (HPC)
environments is usually done with tools such as `SLURM`[@slurm] and
`PBS`[@pbs]. `MyQueue` is a frontend for SLURM/PBS that makes handling of
tasks easy. It has a command-line interface called *mq* with a number of sub-
commands and a Python interface for managing workflows.

The idea behind `MyQueue` is that you have your own queue that you can
submit tasks to and `MyQueue` will handle interactions with your
scheduler (`SLURM` or `PBS`).  Once tasks have finished, they will stay
in your queue so that you can list them and see the status (done, failed,
timed-out or out-of-memory). Tasks will stay in your queue until you
explicitly remove them.  This makes it easy to keep track of your tasks:
If a task is listed as "done" then this will remind you that you need to do
something with the result.  If a task failed then you need to fix something
and resubmit the task.  In this way, `MyQueue` works as a to-do list.

`MyQueue` has a powerful *list* sub-command.  It will by default only show tasks
belonging to the current folder and its sub-folders making it easy to manage
several projects by putting them in separate folders.  Failed tasks will show
an error message read from the relevant line in the error file.  You can
select the tasks you want to list by status, task-id, name or error message.
A task can be marked with a *restarts* number $N$, indicating that `MyQueue`
should restart the task up to $N$ times (with increased resources) if the task
runs out of time or memory.  The increased resources will be more time or more
cores for the out of time and out of memory cases respectively.

`MyQueue` has a Python interface that can be used to define workflows.
In a Python script, you define a dependency tree of tasks that `MyQueue` can
use to submit tasks. It is based on folders and files which makes it very easy
to get started - no system administrator or central database server is needed.
This workflow has been used successfully to drive several high-throughput
screening studies coordinating on the order of 100,000 individual tasks
[@c2db], [@felix].

[@asr] ...

# Acknowledgements

K. S. T. acknowledges funding from the European Research Council (ERC) under
the European Union's Horizon 2020 research and innovation program (Grant
Agreement No. 773122, LIMA).


# References
