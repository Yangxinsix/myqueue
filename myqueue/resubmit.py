from __future__ import annotations
from myqueue.resources import Resources
from myqueue.selection import Selection
from myqueue.task import Task
from myqueue.queue import Queue
from myqueue.submitting import submit


def resubmit(queue: Queue,
             selection: Selection,
             resources: Resources | None,
             force: bool = False) -> None:
    """Resubmit tasks."""
    tasks = []

    for task in selection.select(queue.tasks):
        if task.state in {'queued', 'hold', 'running'}:
            continue

        queue.tasks.remove(task)
        queue.changed.add(task)

        task = Task(task.cmd,
                    deps=task.deps,
                    resources=resources or task.resources,
                    folder=task.folder,
                    restart=task.restart,
                    workflow=task.workflow,
                    creates=task.creates,
                    diskspace=0)
        tasks.append(task)

    submit(queue, tasks, force=force)
