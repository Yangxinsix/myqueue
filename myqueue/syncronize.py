from myqueue.utils import plural
from myqueue.queue import Queue


def sync(queue: Queue) -> None:
    """Syncronize queue with the real world."""
    ids = queue.scheduler.get_ids()
    remove = []
    for id, in queue.connection.execute('SELECT id FROM tasks'):
        if id not in ids:
            remove.append(id)

    if remove:
        if queue.dry_run:
            print(plural(len(remove), 'job'), 'to be removed')
        else:
            queue.remove(remove)
            print(plural(len(remove), 'job'), 'removed')
