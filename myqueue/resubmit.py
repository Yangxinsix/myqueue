from myqueue.resources import Resources
from myqueue.selection import Selection
from myqueue.task import Task


def resubmit(queue,
             selection: Selection,
             resources: Resources | None) -> None:
    """Resubmit failed or timed-out tasks."""
    queue._read()
    tasks = []
    for task in selection.select(queue.tasks):
        if task.state not in {'queued', 'hold', 'running'}:
            queue.tasks.remove(task)
        task.remove_state_file()
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
    queue.submit(tasks, read=False)
