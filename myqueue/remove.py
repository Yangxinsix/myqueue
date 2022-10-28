from __future__ import annotations

from myqueue.pretty import pprint
from myqueue.task import Task
from myqueue.utils import plural
from myqueue.queue import Queue


def remove(queue: Queue,
           tasks: list[Task],
           verbosity: int = 1,
           force: bool = False) -> None:
    """Remove or cancel tasks."""
    ntasks0 = len(tasks)
    tasks = [task for task in tasks if force or not task.workflow]
    ntasks = len(tasks)
    if ntasks < ntasks0:
        print(plural(ntasks0 - ntasks, 'task'), 'part of workflow.  '
              'Use --force to remove.')

    if queue.dry_run:
        if tasks:
            pprint(tasks, verbosity=0, sort='i')
            print(plural(len(tasks), 'task'), 'to be removed')
    else:
        for task in tasks:
            if task.state in ['running', 'hold', 'queued']:
                queue.scheduler.cancel(task.id)
        queue.remove((task.id for task in tasks))
        if verbosity > 0:
            if tasks:
                pprint(tasks, verbosity=0, sort='i')
                print(plural(len(tasks), 'task'), 'removed')
