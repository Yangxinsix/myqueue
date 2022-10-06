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

    held = 0
    released = 0

    if mem > maxmem:
        for task in tasks:
            if task.state == 'queued':
                if task.diskspace > 0:
                    queue.scheduler.hold(task)
                    held += 1
                    task.state = State.hold
                    queue.changed.add(task)
                    mem -= task.diskspace
                    if mem < maxmem:
                        break
    elif mem < maxmem:
        for task in tasks[::-1]:
            if task.state == 'hold' and task.diskspace > 0:
                queue.scheduler.release_hold(task)
                released += 1
                task.state = State.queued
                queue.changed.add(task)
                mem += task.diskspace
                if mem > maxmem:
                    break

    return {name: n
            for name, n in [('held', held), ('released', released)]
            if n > 0}
