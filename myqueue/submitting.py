from __future__ import annotations

import time
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


def submit(queue: Queue,
           tasks: Sequence[Task],
           *,
           done: list[Task] = None,
           max_tasks: int = 1_000_000_000,
           verbosity: int = 1) -> None:
    """Submit tasks to queue.

    Parameters
    ==========
    force: bool
        Ignore and remove name.FAILED files.
    """

    sort_out_dependencies(tasks, queue, done)

    tasks = [task for task in order({task: task.dtasks for task in tasks})
             if task.state == State.undefined]

    tasks = tasks[:max_tasks]

    default_weight = queue.config.default_task_weight
    for task in tasks:
        task.resources.set_default_weight(default_weight)

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

    pprint(submitted, verbosity=0, columns='ifnaIr',
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
                task.id = id
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
        result += reversed(list(nx.topological_sort(dg)))
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
