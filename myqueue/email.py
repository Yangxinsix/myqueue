import smtplib
from email.mime.text import MIMEText
from typing import List, Tuple, Dict
from collections import defaultdict

from myqueue.task import Task


def send_notification(tasks: List[Task],
                      to: str,
                      host: str = '') -> List[Tuple[Task, str]]:
    notifications = []
    for task in tasks:
        character = task.state.value
        if character in 'dMTFC' and 'r' in task.notifications:
            task.notifications = task.notifications.replace('r', '')
            notifications.append((task, 'running'))
        if character in task.notifications:
            task.notifications = task.notifications.replace(character, '')
            notifications.append((task, task.state.name))
    if notifications:
        count: Dict[str, int] = defaultdict(int)
        lines = []
        for task, name in notifications:
            count[name] += 1
            lines.append(f'{name}: {task}')
        subject = 'MyQueue: ' + ', '.join(f'{c} {name}'
                                          for name, c in count.items())
        body = '\n'.join(lines)
        fro = to
        send_mail(subject, body, to, fro, host)
    return notifications


def send_mail(subject: str,
              body: str,
              to: str,
              fro: str,
              host: str = '') -> None:
    """Send an email.

    >>> mail('MyQueue: bla-bla',
    ...      'Hi!\\nHow are you?\\n',
    ...      'you@myqueue.org',
    ...      'me@myqueue.org')
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = to
    msg['To'] = to
    data = msg.as_string()
    if host:
        with smtplib.SMTP(host) as s:  # pragma: no cover
            s.sendmail(msg['From'], [to], data)
