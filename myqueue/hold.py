from __future__ import annotations
from myqueue.queue import Queue


def hold_or_release(queue: Queue) -> dict[str, int]:
    maxmem = queue.config.maximum_diskspace
    mem = 0
    queued = []
    held = []
    sql = (
        'SELECT id, state, diskspace FROM tasks '
        'WHERE diskspace != 0 AND user = ?')
    for id, state, diskspace in queue.sql(sql, [queue.config.user]):
        if state in 'qrFMT':
            mem += diskspace
        if state == 'q':
            queued.append((id, diskspace))
        elif state == 'h':
            held.append((id, diskspace))

    changes: list[tuple[str, int]] = []

    if mem > maxmem:
        for id, diskspace in queued:
            queue.scheduler.hold(id)
            changes.append(('h', id))
            mem -= diskspace
            if mem < maxmem:
                break
    elif mem < maxmem:
        for id, diskspace in held[::-1]:
            queue.scheduler.release_hold(id)
            changes.append(('q', id))
            mem += diskspace
            if mem > maxmem:
                break

    if not changes:
        return {}

    with queue.connection as con:
        con.executemany(
            'UPDATE tasks SET state = ? WHERE id = ?', changes)

    return {changes[0][0]: len(changes)}
