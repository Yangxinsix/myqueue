from __future__ import annotations

import time
from collections import defaultdict
from pathlib import Path
from types import TracebackType
from typing import Sequence, TypeVar, TYPE_CHECKING

from myqueue.pretty import pprint
from myqueue.queue import Queue, sort_out_dependencies
from myqueue.schedulers import Scheduler
from myqueue.states import State
from myqueue.task import Task
from myqueue.utils import plural

if TYPE_CHECKING:
    import rich.progress as progress

TaskName = Path


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


wf = """
        if 0:  # task.workflow:
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
            1 / 0
        else:
            1 / 0
    count.pop(State.undefined, None)
    if count:
        print(', '.join(f'{state}: {n}' for state, n in count.items()))
    if any(state.is_bad() for state in count) and not force:
        print('Use --force to ignore failed tasks.')
"""


def submit(queue: Queue,
           tasks: Sequence[Task],
           *,
           max_tasks: int = 1_000_000_000,
           verbosity: int = 1) -> None:
    """Submit tasks to queue.

    Parameters
    ==========
    force: bool
        Ignore and remove name.FAILED files.
    """

    """
    for task in submitted:
        if task.workflow:
            oldtask = current.get(task.dname)
            if oldtask:
                queue.tasks.remove(oldtask)
                queue.changed.add(oldtask)
    """
    sort_out_dependencies(tasks, queue)

    tasks = [task for task in order({task: task.dtasks for task in tasks})
             if task.state == State.undefined]

    tasks = tasks[:max_tasks]

    ids, ex = submit_tasks(queue.scheduler, tasks, verbosity, queue.dry_run)
    submitted = tasks[:len(ids)]

    if ex:
        nskip = len(tasks) - len(submitted)
        print()
        print('Skipped', plural(nskip, 'task'))

    t = time.time()
    for task, id in zip(submitted, ids):
        task.id = id
        task.state = State.queued
        task.tqueued = t
        # task.deps = [dep.dname for dep in task.dtasks]

    pprint(submitted, 0, 'ifnaIr',
           maxlines=10 if verbosity < 2 else 99999999999999)
    if submitted:
        if queue.dry_run:
            print(plural(len(submitted), 'task'), 'to submit')
        else:
            queue.add(*submitted)
            print(plural(len(submitted), 'task'), 'submitted')

    if ex:
        raise ex


def submit_tasks(scheduler: Scheduler,
                 tasks: Sequence[Task],
                 verbosity: int,
                 dry_run: bool) -> tuple[list[int],
                                         Exception | KeyboardInterrupt | None]:
    """Submit tasks."""
    import rich.progress as progress

    ids = []
    ex = None

    pb: progress.Progress | NoProgressBar

    if verbosity and len(tasks) > 1:
        pb = progress.Progress('[progress.description]{task.description}',
                               progress.BarColumn(),
                               progress.MofNCompleteColumn())
    else:
        pb = NoProgressBar()

    with pb:
        try:
            pid = pb.add_task('Submitting tasks:', total=len(tasks))
            for task in tasks:
                id = scheduler.submit(
                    task,
                    dry_run,
                    verbosity >= 2)
                ids.append(id)
                pb.advance(pid)
        except (Exception, KeyboardInterrupt) as x:
            ex = x

    return ids, ex


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
