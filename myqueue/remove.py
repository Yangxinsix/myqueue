import time

from myqueue.pretty import pprint
from myqueue.selection import Selection
from myqueue.task import Task
from myqueue.utils import plural
from myqueue.queue import Queue


def remove(queue: Queue, selection: Selection) -> None:
    """Remove or cancel tasks."""

    queue._read()

    tasks = selection.select(queue.tasks)
    tasks = queue.find_depending(tasks)

    queue._remove(tasks)


def _remove(queue: Queue, tasks: list[Task]) -> None:
    t = time.time()
    for task in tasks:
        if task.tstop is None:
            task.tstop = t  # XXX is this for dry_run only?

    if queue.dry_run:
        if tasks:
            pprint(tasks, 0)
            print(plural(len(tasks), 'task'), 'to be removed')
    else:
        if queue.verbosity > 0:
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
