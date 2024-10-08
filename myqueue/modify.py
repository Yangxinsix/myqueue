from __future__ import annotations

from myqueue.email import configure_email
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.states import State


def modify(queue: Queue,
           selection: Selection,
           newstate: State,
           email: set[State],
           db_only: bool=False) -> None:
    """Modify task(s)."""
    tasks = queue.select(selection)

    if email != {State.undefined}:
        configure_email(queue.config)
        if queue.dry_run:
            print(tasks, email)
        else:
            n = ''.join(state.value for state in email)
            with queue.connection as con:
                con.executemany(
                    f'UPDATE tasks SET notifications = "{n}" WHERE id = ?',
                    [(task.id,) for task in tasks])

    if newstate == State.undefined:
        return
    
    if not db_only:
        if newstate == State.queued:
            oldstate = State.hold
            operation = queue.scheduler.release_hold
        else:
            assert newstate == State.hold
            oldstate = State.queued
            operation = queue.scheduler.hold

        if any(task.state != oldstate for task in tasks):
            raise ValueError(f'Initial state must be: {oldstate}!')

    if not queue.dry_run:
        if not db_only:
            for task in tasks:
                operation(task.id)
        
        old_states = [task.state for task in tasks]

        with queue.connection as con:
            con.executemany(
                f'UPDATE tasks SET state = "{newstate.value}" WHERE id = ?',
                [(task.id,) for task in tasks])

    for old_state, task in zip(old_states, tasks):
        print(f'Task {task.id}: state changed from {old_state} -> {newstate}')
