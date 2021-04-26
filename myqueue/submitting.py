import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Sequence
from graphlib import TopologicalSorter

from myqueue.progress import progress_bar
from myqueue.scheduler import Scheduler
from myqueue.task import Task
from myqueue.virtenv import find_activation_scripts

from .states import State

TaskID = Path


class DependencyError(Exception):
    """Bad dependency."""


def find_dependency(dname, current, new, force=False):
    if dname in current:
        task = current[dname]
        if task.state.is_bad():
            if force:
                if dname not in new:
                    raise DependencyError()
                task = new[dname].task
    elif dname in new:
        task = new[dname].task
    else:
        raise DependencyError()
    return task


def mark(task, children):
    for child in children[task]:
        child.state = State.FAILED
        mark(child, children)


def remove_bad_tasks(tasks):
    children = defaultdict(list)
    for task in tasks:
        for dep in task.dtasks:
            children[dep].append(task)

    for task in tasks:
        if task.state.is_bad():
            mark(task, children)

    return [task for task in tasks if not task.state.is_bad()]


def submit_tasks(scheduler: Scheduler,
                 tasks: Sequence[Task],
                 current: Dict[Path, Task],
                 force: bool,
                 max_tasks: int,
                 verbosity: int,
                 dry_run: bool) -> Tuple[List[Task],
                                         List[Task],
                                         Optional[Exception]]:

    new = {task.dname: task for task in tasks}

    print(new)

    count = defaultdict(int)
    submit = []
    for task in tasks:
        if task.dname in current:
            task.state = current[task.dname].state
        else:
            task.state = task.read_state_file()

        count[task.state] += 1

        if task.state != 'UNDEFINED' or force:
            submit.append(task)

    print(count)

    count.pop(State.UNDEFINED, None)
    if count:
        print('State    number of tasks')
        for state, n in sorted(count.items()):
            print(state, n)

    if any(state.is_bad() for state in count) and not force:
        print('Use --force to ignore and remove the .FAILED files.')

    for task in submit:
        task.deps = []
        for dname in task.deps:
            dep = find_dependency(dname, current, new, force)
            if dep.state != 'done':
                task.deps.append(dep)

    submit = remove_bad_tasks(submit)

    print(submit)
    submit = list(TopologicalSorter({task: task.dtasks
                                     for task in submit}).static_order())

    submit = submit[:max_tasks]

    t = time.time()
    for task in submit:
        task.state = State.queued
        task.tqueued = t

    activation_scripts = find_activation_scripts([task.folder
                                                  for task in submit])
    for task in submit:
        task.activation_script = activation_scripts.get(task.folder)

    pb = progress_bar(len(submit),
                      f'Submitting {len(submit)} tasks:',
                      verbosity and len(submit) > 1)
    submitted = []
    ex = None
    try:
        for task in submit:
            scheduler.submit(
                task,
                dry_run,
                verbosity >= 2)
            submitted.append(task)
            next(pb)
    except Exception as x:
        ex = x

    return submitted, submit[len(submitted):], ex
