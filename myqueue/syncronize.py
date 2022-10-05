from myqueue.utils import plural
from myqueue.states import State


def sync(queue) -> None:
    """Syncronize queue with the real world."""
    queue._read()
    in_the_queue = {'running', 'hold', 'queued'}
    ids = queue.scheduler.get_ids()
    cancel = []
    remove = []
    for task in queue.tasks:
        if task.id not in ids:
            if task.state in in_the_queue:
                cancel.append(task)
            if not task.folder.is_dir():
                remove.append(task)

    if cancel:
        if queue.dry_run:
            print(plural(len(cancel), 'job'), 'to be canceled')
        else:
            for task in cancel:
                task.state = State.CANCELED
                queue.changed.add(task)
            print(plural(len(cancel), 'job'), 'canceled')

    if remove:
        if queue.dry_run:
            print(plural(len(remove), 'job'), 'to be removed')
        else:
            for task in remove:
                queue.tasks.remove(task)
                queue.changed.add(task)
            print(plural(len(remove), 'job'), 'removed')
