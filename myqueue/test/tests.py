import os
import tempfile
import time
from typing import List
from pathlib import Path

from myqueue.cli import main
from myqueue.config import read_config


LOCAL = True


def mq(cmd):
    args = cmd.split()
    args[1:1] = ['--traceback']
    return main(args)


all_tests = {}


def test(func):
    all_tests[func.__name__] = func
    return func


def states():
    return ''.join(job.state[0] for job in mq('list'))


tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-',
                               dir=str(Path.home())))


def wait()-> None:
    t0 = time.time()
    timeout = 10.0 if LOCAL else 300.0
    sleep = 0.1 if LOCAL else 3.0
    while mq('list -s qr -qq'):
        time.sleep(sleep)
        if time.time() - t0 > timeout:
            raise TimeoutError


def run_tests(tests: List[str], local: bool, exclude: List[str]):
    global LOCAL
    LOCAL = local
    print('\nRunning tests in', tmpdir)
    os.chdir(str(tmpdir))
    os.environ['MYQUEUE_HOME'] = str(tmpdir)
    cfg = read_config()
    os.environ['MYQUEUE_DEBUG'] = 'local' if local else cfg['queue']

    if not tests:
        tests = list(all_tests)

    for test in exclude:
        tests.remove(test)

    N = 79
    for name in tests:
        print()
        print('#' * N)
        print(' Running "{}" test '.format(name).center(N, '#'))
        print('#' * N)
        print()

        all_tests[name]()

        mq('rm -s qrdFTCM . -r')

        for f in tmpdir.glob('**/*'):
            f.unlink()

    tmpdir.rmdir()


@test
def submit():
    mq('submit time.sleep+2')
    mq('submit echo+hello -d time.sleep+2')
    wait()
    for job in mq('list'):
        assert job.state == 'done'


@test
def fail():
    mq('submit time.sleep+a')
    mq('submit echo+hello -d time.sleep+a')
    wait()
    assert states() == 'FC'
    mq('resubmit -sF .')
    wait()
    assert states() == 'CF'


@test
def fail2():
    mq('submit time.sleep+a --workflow')
    wait()
    assert states() == 'F'
    mq('remove --state F .')
    mq('submit time.sleep+a --workflow')
    wait()
    assert states() == ''


@test
def timeout():
    t = 3 if LOCAL else 120
    mq('submit sleep@1:1s -a {}'.format(t))
    mq('submit echo+hello -d sleep+{}'.format(t))
    wait()
    mq('resubmit -sT . -R 1:5m')
    wait()
    assert states() == 'Cd'


@test
def timeout2():
    t = 3 if LOCAL else 120
    mq('submit sleep@1:{}s --restart -a {}'.format(t // 3 * 2, t))
    mq('submit echo+hello -d sleep+{}'.format(t))
    wait()
    mq('kick')
    wait()
    assert states() == 'dd'


@test
def oom():
    mq('submit myqueue.test.oom --restart -a {}'.format(LOCAL))
    wait()
    assert states() == 'M'
    mq('kick')
    wait()
    assert states() == 'd'


wf = """
from myqueue.task import task
def create_tasks():
    t1 = task('sleep+3')
    return [t1, task('echo+hello', deps=[t1])]
"""


@test
def workflow():
    mq('submit sleep+3@1:1m -w')
    time.sleep(2)
    Path('wf.py').write_text(wf)
    mq('workflow wf.py .')
    wait()
    assert states() == 'dd'


wf2 = """
from myqueue.task import task
def create_tasks():
    return [task('echo+hi', diskspace=1) for _ in range(4)]
"""


@test
def workflow2():
    Path('wf2.py').write_text(wf2)
    mq('workflow wf2.py .')
    mq('kick')
    wait()
    assert states() == 'dddd'
