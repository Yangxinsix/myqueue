from __future__ import annotations
from myqueue.task import Task
from myqueue.states import State
from myqueue.queue import Queue


def hold_or_release(queue: Queue,
                    tasks: list[Task]) -> dict[str, int]:
    maxmem = queue.config.maximum_diskspace
    mem = 0
    for task in tasks:
        if task.state in {'queued', 'running',
                          'FAILED', 'TIMEOUT', 'MEMORY'}:
            mem += task.diskspace

    changes: list[tuple[str, int]] = []

    if mem > maxmem:
        for task in tasks:
            if task.state == 'queued' and task.diskspace > 0:
                queue.scheduler.hold(task)
                changes.append(('h', task.id))
                task.state = State.hold
                mem -= task.diskspace
                if mem < maxmem:
                    break
    elif mem < maxmem:
        for task in tasks[::-1]:
            if task.state == 'hold' and task.diskspace > 0:
                queue.scheduler.release_hold(task)
                changes.append(('q', task.id))
                task.state = State.queued
                mem += task.diskspace
                if mem > maxmem:
                    break

    if not changes:
        return {}

    with queue.connection as con:
        con.executemany(
            'UPDATE tasks SET state = ? WHERE id = ?', changes)

    return {changes[0][0]: len(changes)}
