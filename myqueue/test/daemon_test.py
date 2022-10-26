from __future__ import annotations
import functools
# import socket
# import time

from myqueue.daemon import perform_daemon_action


def test_daemon(mq, capsys):
    cmd = functools.partial(perform_daemon_action,
                            mq.config)
    cmd('status')
    cmd('stop')
    expected = ['Not running',
                'Not running!']
    # We have to skip this because it forks the test suite which will
    # then run twice!
    """
    host = socket.gethostname()
    pid = cmd('start')
    cmd('start')
    cmd('status')
    cmd('stop')
    time.sleep(0.2)
    cmd('status')
    expected += [
        f'PID: {pid}',
        'Already running',
        f'Running on {host} with pid={pid}',
        'Not running']
    """
    assert capsys.readouterr().out == '\n'.join(expected + [''])
