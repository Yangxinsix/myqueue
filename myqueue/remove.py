from __future__ import annotations
import time

from myqueue.pretty import pprint
from myqueue.task import Task
from myqueue.utils import plural
from myqueue.queue import Queue


def remove(queue: Queue,
           tasks: list[Task],
           verbosity: int = 1) -> None:
    """Remove or cancel tasks."""
    t = time.time()
    for task in tasks:
        if task.tstop is None:
            task.tstop = t  # XXX is this for dry_run only?

    if queue.dry_run:
        if tasks:
            pprint(tasks, 0)
            print(plural(len(tasks), 'task'), 'to be removed')
    else:
        if verbosity > 0:
            if tasks:
                pprint(tasks, 0)
                print(plural(len(tasks), 'task'), 'removed')
        for task in tasks:
            if task.state in ['running', 'hold', 'queued']:
                queue.scheduler.cancel(task)
            queue.tasks.remove(task)
            # XXX why cancel?
            task.cancel_dependents(queue.tasks, time.time())
            queue.changed.add(task)
