from __future__ import annotations
from myqueue.states import State
from myqueue.email import send_notification
from myqueue.pretty import pprint
from myqueue.utils import plural
from myqueue.queue import Queue
from myqueue.submitting import submit
from myqueue.hold import hold_or_release


def kick(queue: Queue, verbosity: int = 1) -> dict[str, int]:
    """Kick the system.

    * send email notifications
    * restart timed-out tasks
    * restart out-of-memory tasks
    * release/hold tasks to stay under *maximum_total_task_weight*
    """
    result = {}

    ndct = queue.config.notifications
    if ndct:
        notifications = send_notification(queue, **ndct)
        result['notifications'] = len(notifications)

    tasks = []
    sql = 'state IN ("T", "M") AND restart != 0 AND user = ?'
    for task in queue.tasks(sql, [queue.config.user]):
        nodes = queue.config.nodes or [('', {'cores': 1})]
        task.resources = task.resources.bigger(task.state, nodes)
        task.restart -= 1
        tasks.append(task)

    if tasks:
        if not queue.dry_run:
            with queue.connection as con:
                con.executemany('UPDATE tasks SET restart = 0 WHERE id = ?',
                                [(task.id,) for task in tasks])
        ids = list(queue.find_dependents(task.id for task in tasks))
        queue.cancel_dependents(ids)
        for id in ids:
            tasks.append(queue.tasks('id = ?', [id])[0])

        if queue.dry_run:
            pprint(tasks)
        else:
            if verbosity > 0:
                print('Restarting', plural(len(tasks), 'task'))
            for task in tasks:
                task.error = ''
                task.state = State.undefined
            submit(queue, tasks)
        result['restarts'] = len(tasks)

    result.update(hold_or_release(queue))

    return result
