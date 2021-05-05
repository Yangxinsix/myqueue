import smtplib
import sys
from collections import defaultdict
from email.mime.text import MIMEText
from typing import Dict, List, Tuple

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
              host: str) -> None:
    """Send an email.

    >>> send_mail('MyQueue: bla-bla',
    ...          'Hi!\\nHow are you?\\n',
    ...          'you@myqueue.org',
    ...          'me@myqueue.org',
    ...          'test.smtp.org')
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = fro
    msg['To'] = to
    data = msg.as_string()
    if host != 'test.smtp.org':
        with smtplib.SMTP(host) as s:
            s.sendmail(msg['From'], [to], data)


if __name__ == '__main__':
    to, host = sys.argv[1:]
    send_mail('Test email from myqueue',
              'Testing ...\n',
              to, to, host)
