from __future__ import annotations
from myqueue.selection import Selection
from myqueue.states import State
from myqueue.email import configure_email
from myqueue.queue import Queue


def modify(queue: Queue,
           selection: Selection,
           newstate: State,
           email: set[State]) -> None:
    """Modify task(s)."""
    tasks = selection.select(queue.tasks)

    if email != {State.undefined}:
        configure_email(queue.config)
        for task in tasks:
            if queue.dry_run:
                print(task, email)
            else:
                task.notifications = ''.join(state.value
                                             for state in email)
                queue.changed.add(task)

    if newstate != State.undefined:
        for task in tasks:
            if task.state == 'hold' and newstate == 'queued':
                if queue.dry_run:
                    print('Release:', task)
                else:
                    queue.scheduler.release_hold(task)
            elif task.state == 'queued' and newstate == 'hold':
                if queue.dry_run:
                    print('Hold:', task)
                else:
                    queue.scheduler.hold(task)
            elif task.state == 'FAILED' and newstate in ['MEMORY',
                                                         'TIMEOUT']:
                if queue.dry_run:
                    print('FAILED ->', newstate, task)
                else:
                    task.state = newstate
                    queue.changed.add(task)
            else:
                raise ValueError(f'Can\'t do {task.state} -> {newstate}!')
            print(f'{task.state} -> {newstate}: {task}')
            task.state = newstate
            queue.changed.add(task)
