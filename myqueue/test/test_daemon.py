from myqueue.daemon import perform_action
import functools


def test_daemon(mq):
    cmd = functools.partial(perform_action, mq.config.home / '.myqueue')
    cmd('status')
    cmd('stop')
    cmd('start')
    cmd('start')
    cmd('status')
    cmd('stop')
    cmd('status')
