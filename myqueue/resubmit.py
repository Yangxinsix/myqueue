from __future__ import annotations
from myqueue.resources import Resources
from myqueue.selection import Selection
from myqueue.task import Task
from myqueue.queue import Queue
from myqueue.submitting import submit


def resubmit(queue: Queue,
             selection: Selection,
             resources: Resources | None,
             remove: bool = False) -> None:
    """Resubmit tasks."""
    tasks = []
    ids = []
    for task in queue.select(selection):
        if task.state in {'queued', 'hold', 'running'}:
            continue

        ids.append(task.id)
        task = Task(task.cmd,
                    deps=task.deps,
                    resources=resources or task.resources,
                    folder=task.folder,
                    restart=task.restart,
                    workflow=task.workflow,
                    creates=task.creates)
        tasks.append(task)

    if remove and not queue.dry_run:
        queue.remove(ids)

    submit(queue, tasks)
