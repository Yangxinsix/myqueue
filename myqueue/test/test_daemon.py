from myqueue.daemon import perform_action
import functools
import time


def test_daemon(mq, capsys):
    cmd = functools.partial(perform_action,
                            mq.config.home / '.myqueue')
    cmd('status')
    cmd('stop')
    pid = cmd('start')
    cmd('start')
    cmd('status')
    cmd('stop')
    time.sleep(0.2)
    cmd('status')
    assert capsys.readouterr().out == '\n'.join(
        ['Not running',
         'Not running',
         f'PID: {pid}',
         'Already running',
         f'Running on Hjem with pid={pid}',
         'Not running',
         ''])
