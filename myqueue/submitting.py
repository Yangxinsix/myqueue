from __future__ import annotations

import os
import time
from collections import defaultdict
from pathlib import Path
from types import TracebackType
from typing import Sequence, TypeVar, TYPE_CHECKING

from myqueue.pretty import pprint
from myqueue.queue import Queue
from myqueue.schedulers import Scheduler
from myqueue.states import State
from myqueue.task import Task
from myqueue.utils import plural

if TYPE_CHECKING:
    import rich.progress as progress

TaskName = Path


class DependencyError(Exception):
    """Bad dependency."""


def find_dependency(dname: TaskName,
                    current: dict[TaskName, Task],
                    new: dict[TaskName, Task],
                    force: bool = False) -> Task:
    """Convert dependency name to task."""
    if dname in current:
        task = current[dname]
        if task.state.is_bad():
            if force:
                if dname not in new:
                    raise DependencyError(dname)
                task = new[dname]
    elif dname in new:
        task = new[dname]
    else:
        raise DependencyError(dname)
    return task


def mark_children(task: Task, children: dict[Task, list[Task]]) -> None:
    """Mark children of task as FAILED."""
    for child in children[task]:
        child.state = State.FAILED
        mark_children(child, children)


def remove_bad_tasks(tasks: list[Task]) -> list[Task]:
    """Create list without bad dependencies."""
    children = defaultdict(list)
    for task in tasks:
        for dep in task.dtasks:
            children[dep].append(task)

    for task in list(children):
        if task.state.is_bad():
            mark_children(task, children)

    return [task for task in tasks if not task.state.is_bad()]


def submit(queue: Queue,
           tasks: Sequence[Task],
           *,
           force: bool = False,
           max_tasks: int = 1_000_000_000,
           verbosity: int = 1) -> None:
    """Submit tasks to queue.

    Parameters
    ==========
    force: bool
        Ignore and remove name.FAILED files.
    """

    current = {task.dname: task for task in queue.tasks}

    submitted, skipped, ex = submit_tasks(
        queue.scheduler, tasks, current,
        force, max_tasks,
        verbosity, queue.dry_run)

    for task in submitted:
        if task.workflow:
            oldtask = current.get(task.dname)
            if oldtask:
                queue.tasks.remove(oldtask)
                queue.changed.add(oldtask)

    if 'MYQUEUE_TESTING' in os.environ:
        if any(task.cmd.args == ['SIMULATE-CTRL-C'] for task in submitted):
            raise KeyboardInterrupt

    queue.tasks += submitted
    queue.changed.update(submitted)

    if ex:
        print()
        print('Skipped', plural(len(skipped), 'task'))

    pprint(submitted, 0, 'ifnaIr',
           maxlines=10 if verbosity < 2 else 99999999999999)
    if submitted:
        if queue.dry_run:
            print(plural(len(submitted), 'task'), 'to submit')
        else:
            print(plural(len(submitted), 'task'), 'submitted')

    if ex:
        raise ex


def submit_tasks(scheduler: Scheduler,
                 tasks: Sequence[Task],
                 current: dict[Path, Task],
                 force: bool,
                 max_tasks: int,
                 verbosity: int,
                 dry_run: bool) -> tuple[list[Task],
                                         list[Task],
                                         Exception | KeyboardInterrupt | None]:
    """Submit tasks."""
    import rich.progress as progress

    new = {task.dname: task for task in tasks}

    count: dict[State, int] = defaultdict(int)
    submit = []
    for task in tasks:
        if task.workflow:
            if task.dname in current:
                task.state = current[task.dname].state
            else:
                if task.state == State.undefined:
                    if task.check_creates_files():
                        task.state = State.done
        count[task.state] += 1

        if task.state == State.undefined:
            submit.append(task)
        elif task.state.is_bad() and force:
            task.state = State.undefined
            submit.append(task)

    count.pop(State.undefined, None)
    if count:
        print(', '.join(f'{state}: {n}' for state, n in count.items()))
    if any(state.is_bad() for state in count) and not force:
        print('Use --force to ignore failed tasks.')

    for task in submit:
        task.dtasks = []
        for dname in task.deps:
            dep = find_dependency(dname, current, new, force)
            if dep.state != 'done':
                task.dtasks.append(dep)

    n = len(submit)
    submit = remove_bad_tasks(submit)
    n = n - len(submit)
    if n > 0:
        print('Skipping', plural(n, 'task'), '(bad dependency)')

    submit = [task for task in order({task: task.dtasks for task in submit})
              if task.state == State.undefined]

    submit = submit[:max_tasks]

    t = time.time()
    for task in submit:
        task.state = State.queued
        task.tqueued = t
        task.deps = [dep.dname for dep in task.dtasks]

    venv = os.environ.get('VIRTUAL_ENV')
    if venv:
        activation_script = Path(venv) / 'bin/activate'
        for task in submit:
            task.activation_script = activation_script

    submitted = []
    ex = None

    pb: progress.Progress | NoProgressBar

    if verbosity and len(submit) > 1:
        pb = progress.Progress('[progress.description]{task.description}',
                               progress.BarColumn(),
                               progress.MofNCompleteColumn())
    else:
        pb = NoProgressBar()

    with pb:
        try:
            id = pb.add_task('Submitting tasks:', total=len(submit))
            for task in submit:
                scheduler.submit(
                    task,
                    dry_run,
                    verbosity >= 2)
                submitted.append(task)
                pb.advance(id)
        except (Exception, KeyboardInterrupt) as x:
            ex = x

    return submitted, submit[len(submitted):], ex


T = TypeVar('T')


def order(nodes: dict[T, list[T]]) -> list[T]:
    """Depth first.

    >>> order({1: [2], 2: [], 3: [4], 4: []})
    [2, 1, 4, 3]
    """
    import networkx as nx  # type: ignore
    result: list[T] = []
    g = nx.Graph(nodes)
    for component in nx.connected_components(g):
        dg = nx.DiGraph({node: nodes[node]
                         for node in component
                         if node in nodes})
        order = nx.topological_sort(dg)
        result += reversed(list(order))
    return result


class NoProgressBar:
    """Dummy progress-bar."""
    def __enter__(self) -> NoProgressBar:
        return self

    def __exit__(self,
                 type: Exception,
                 value: Exception,
                 tb: TracebackType) -> None:
        pass

    def add_task(self, text: str, total: int) -> progress.TaskID:
        import rich.progress as progress
        return progress.TaskID(0)

    def advance(self, id: progress.TaskID) -> None:
        pass
