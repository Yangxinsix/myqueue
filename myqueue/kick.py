from myqueue.states import State
from myqueue.email import send_notification
from myqueue.pretty import pprint
from myqueue.utils import plural


def kick(queueu) -> dict[str, int]:
    """Kick the system.

    * Send email notifications
    * restart timed-out tasks
    * restart out-of-memory tasks
    * release/hold tasks to stay under *maximum_diskspace*
    """
    queueu._read()

    mytasks = [task for task in queueu.tasks
               if task.user == queueu.config.user]

    result = {}

    ndct = queueu.config.notifications
    if ndct:
        notifications = send_notification(mytasks, **ndct)
        queueu.changed.update(task for task, statename in notifications)
        result['notifications'] = len(notifications)

    tasks = []
    for task in mytasks:
        if task.state in ['TIMEOUT', 'MEMORY'] and task.restart:
            nodes = queueu.config.nodes or [('', {'cores': 1})]
            if not queueu.dry_run:
                task.resources = task.resources.bigger(task.state, nodes)
                task.restart -= 1
            tasks.append(task)

    if tasks:
        tasks = queueu.find_depending(tasks)
        if queueu.dry_run:
            pprint(tasks)
        else:
            if queueu.verbosity > 0:
                print('Restarting', plural(len(tasks), 'task'))
            for task in tasks:
                queueu.tasks.remove(task)
                task.error = ''
                task.id = '0'
                task.state = State.undefined
            queueu.submit(tasks, read=False)
        result['restarts'] = len(tasks)

    result.update(queueu.hold_or_release(mytasks))

    return result
