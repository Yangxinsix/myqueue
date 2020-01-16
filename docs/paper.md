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
 - name: CAMD, Department of Physics, Technical University of Denmark, 2800 Kgs. Lyngby, Denmark
   index: 1
date: 11 November 2019
bibliography: paper.bib
---


# Summary

Task scheduling and workload management on high-performance computing
environments is usually done with tools such as `SLURM` [@slurm].
[MyQueue](https://myqueue.readthedocs.io/) is a front-end for schedulers that
makes handling of tasks easy. It has a command-line interface called *mq* with
a number of sub-commands and a Python interface for managing workflows.
Currently, the following schedulers are supported:
[SLURM](https://en.m.wikipedia.org/wiki/Slurm_Workload_Manager),
[PBS](https://en.m.wikipedia.org/wiki/Portable_Batch_System), and
[LSF](https://en.m.wikipedia.org/wiki/Platform_LSF).

The idea behind `MyQueue` is to define a personal queue that the
user can interact with in an easy and efficient way while `MyQueue` handles
the interaction with the scheduler. Finished tasks will stay in the personal
queue until they are explicitly removed so they can be listed with their
status (done, failed, timed-out, or out-of-memory). This makes it easy to keep
track of your tasks: If a task is listed as "done", it reminds you that some
action should be taken, e.g., the result of the task should be checked. If a
task failed then you need to fix something and resubmit the task. In this
sense, `MyQueue` works as a to-do list.

`MyQueue` has a convenient *list* sub-command.  It will by default only
show tasks belonging to the current folder and its sub-folders, making it easy
to manage several projects by putting them in separate folders.  Failed tasks
will show a short error message read from the relevant line in the error file.
You can select the tasks you want to list by status, task-id, name, or error
message. A task can be marked with a *restarts* number $N$, indicating that
`MyQueue` should restart the task up to $N$ times (with increased resources)
if the task runs out of time or memory. Increased resources means longer time
or more cores for the timed-out and out-of-memory cases, respectively.

The `MyQueue` *submit* sub-command makes it easy to submit thousands
of tasks in a single command. As input *submit* takes a shell script, Python
script, or Python module and executes the script/module in a number of folders.
This makes it easy to submit a large number of tasks quickly. The *list*
sub-command can then be used to monitor the execution of the tasks. Together
with the *resubmit* sub-command it becomes easy to resubmit any tasks that
might have failed. This example show how the sub-commands of `MyQueue`
synergize and increase the efficiency of the user.

`MyQueue` has a simple Python interface that can be used to define
workflows. A Python script defines a dependency tree of tasks that `MyQueue`
can use to submit tasks without user involvement. The dependencies take the
form "if task X is done then submit task Y".  `MyQueue` works directly with
folders and files, which makes it simple to use and easy to get started.

Compared to the current state of the field `MyQueue` distinguishes
itself by focusing *not* on automatic handling of crashes but *only*
on the single problem of submitting and managing thousands of tasks.
In the scientific field of the authors, atomic-scale simulations,
commonly used workflow managers are
[AiiDA](http://www.aiida.net) [@aiida] and
[Fireworks](https://materialsproject.github.io/fireworks) [@fireworks].
Fireworks' centralized server model is advantageous when coordinating
tasks distributed between multiple users.  In constrast to Fireworks,
`MyQueue` is installed per user, is completely decentralized, and
cannot coordinate tasks between multiple users.  AiiDA is a fully
automatic workflow tool designed to ensure data provenance. In contrast
to AiiDA, `MyQueue` does not handle data provenance and does not focus
on the automization of the workflow process.  These design decisions
can be seen both as a drawback and an advantage depending on the use
case, but in any case makes `MyQueue` easier to learn.  To summarize,
`MyQueue` is a personal, decentralized, and lightweight front-end for
schedulers with support for submitting workflows. It requires no
system administrator and no database server.

`MyQueue` is useful for high-throughput computations, which require automatic
submission of thousands of interdependent jobs. For example, `MyQueue` has
been used to drive high-throughput screening studies coordinating on the
order of 100,000 individual tasks [@c2db], [@felix].  `MyQueue` is also used
by the [Atomic Simulation Recipes](https://asr.readthedocs.io/) project, which
is a library of tasks for atomic simulations.

# Acknowledgments

K. S. T. acknowledges funding from the European Research Council (ERC) under
the European Union's Horizon 2020 research and innovation program (Grant
Agreement No. 773122, LIMA).


# References
