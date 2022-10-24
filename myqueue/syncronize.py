from myqueue.queue import Queue
from myqueue.utils import plural


def sync(queue: Queue) -> None:
    """Syncronize queue with the real world."""
    ids = queue.scheduler.get_ids()
    remove = []

    sql = 'SELECT id FROM tasks WHERE state IN ("q", "h", "r")'
    for id, in queue.sql(sql):
        if id not in ids:
            remove.append(id)

    root = queue.folder.parent
    for id, folder in queue.sql('SELECT id, folder FROM tasks'):
        if not (root / folder).is_dir():
            remove.append(id)

    print('REMOVE', remove)
    if remove:
        if queue.dry_run:
            print(plural(len(remove), 'job'), 'to be removed')
        else:
            queue.remove(remove)
            print(plural(len(remove), 'job'), 'removed')
