import smtplib
from email.mime.text import MIMEText
from typing import List, Tuple
from collections import defaultdict

from myqueue.task import Task


def send_notification_email(tasks: List[Task],
                            to: str,
                            host: str = '') -> List[Tuple[Task, str]]:
    notifications = []
    for task in tasks:
        character = task.status.value
        if character in task.email:
            if task.state.is_bad() and 'r' in task.email:
                task.email = task.email.remove('r')
                notifications.append((task, 'running'))
            task.email = task.email.remove(character)
            notifications.append((task, task.state.name))
    if notifications:
        count = defaultdict(int)
        lines = []
        for task, name in notifications:
            count[name] += 1
            lines.append(f'{name}: {task}')
        subject = 'MyQueue: ' + ', '.join(f'{c} {name}'
                                          for name, c in count.items())
        body = '\n'.join(lines)
        fro = to
        mail(subject, body, to, fro, host)
    return notifications


class TestSMTP:
    def sendmail(self, fro: str, to: List[str], msg: str):
        pass

    def quit(self):
        pass


def mail(subject: str, body: str, to: str, fro: str, host: str = '') -> None:
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
    if host:
        s = smtplib.SMTP(host)
    else:
        s = TestSMTP()
    s.sendmail(msg['From'], [to], msg.as_string())
    s.quit()
