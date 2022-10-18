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

    * Send email notifications
    * restart timed-out tasks
    * restart out-of-memory tasks
    * release/hold tasks to stay under *maximum_diskspace*
    """
    mytasks = [task for task in queue.tasks
               if task.user == queue.config.user]

    result = {}

    ndct = queue.config.notifications
    if ndct:
        notifications = send_notification(mytasks, **ndct)
        result['notifications'] = len(notifications)

    tasks = []
    for task in mytasks:
        if task.state in ['TIMEOUT', 'MEMORY'] and task.restart:
            nodes = queue.config.nodes or [('', {'cores': 1})]
            if not queue.dry_run:
                task.resources = task.resources.bigger(task.state, nodes)
                task.restart -= 1
            tasks.append(task)

    if tasks:
        tasks = queue.find_depending(tasks)
        if queue.dry_run:
            pprint(tasks)
        else:
            if verbosity > 0:
                print('Restarting', plural(len(tasks), 'task'))
            for task in tasks:
                queue.tasks.remove(task)
                task.error = ''
                task.id = '0'
                task.state = State.undefined
            submit(queue, tasks)
        result['restarts'] = len(tasks)

    result.update(hold_or_release(queue, mytasks))

    return result
