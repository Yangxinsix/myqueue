from __future__ import annotations
from myqueue.queue import Queue
from math import inf


def hold_or_release(queue: Queue) -> dict[str, int]:
    maxweight = queue.config.maximum_total_task_weight
    if maxweight == inf:
        return {}
    totweight = 0
    queued = []
    held = []
    sql = (
        'SELECT id, state, weight FROM tasks '
        'WHERE state IN ("q", "r", "h", "F", "M", "T") AND '
        'weight != 0 AND user = ?')
    for id, state, weight in queue.sql(sql, [queue.config.user]):
        if state in 'qrFMT':
            totweight += weight
        if state == 'q':
            queued.append((id, weight))
        elif state == 'h':
            held.append((id, weight))

    changes: list[tuple[str, int]] = []

    if totweight > maxweight:
        for id, weight in queued:
            queue.scheduler.hold(id)
            changes.append(('h', id))
            totweight -= weight
            if totweight < maxweight:
                break
    elif totweight < maxweight:
        for id, weight in held[::-1]:
            queue.scheduler.release_hold(id)
            changes.append(('q', id))
            totweight += weight
            if totweight > maxweight:
                break

    if not changes:
        return {}

    with queue.connection as con:
        con.executemany(
            'UPDATE tasks SET state = ? WHERE id = ?', changes)

    return {changes[0][0]: len(changes)}
