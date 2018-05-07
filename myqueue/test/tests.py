import os
import tempfile
import time
from typing import List
from pathlib import Path

from myqueue.cli import main


SLOW = False


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
    timeout = 300.0 if SLOW else 10.0
    sleep = 3.0 if SLOW else 0.1
    while mq('list -s qr -qq'):
        time.sleep(sleep)
        if time.time() - t0 > timeout:
            raise TimeoutError


def run_tests(tests: List[str], slow: bool):
    global SLOW
    SLOW = slow
    print('\nRunning tests in', tmpdir)
    os.chdir(str(tmpdir))
    # os.environ['MYQUEUE_HOME'] = str(tmpdir)
    os.environ['MYQUEUE_DEBUG'] = 'yes!'

    if not tests:
        tests = list(all_tests)

    N = 79
    for name in tests:
        print()
        print('#' * N)
        print(' Running "{}" test '.format(name).center(N, '#'))
        print('#' * N)
        print()

        all_tests[name]()

        mq('rm -s qrdFTC . -r')

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
    mq('submit myqueue.test.fail+2')
    mq('submit echo+hello -d myqueue.test.fail+2')
    wait()
    assert states() == 'FC'
    mq('resubmit -sF .')
    wait()
    assert states() == 'CF'


@test
def timeout():
    T = '120' if SLOW else '3'
    mq('submit sleep@1x1s -a ' + T)
    mq('submit echo+hello -d sleep+' + T)
    wait()
    mq('resubmit -sT . -R 1x5m')
    wait()
    assert states() == 'Cd'


wf = """
from myqueue.job import Job
def workflow():
    j1 = Job('sleep+3')
    return [j1, Job('echo+hello', deps=[j1])]
"""


@test
def workflow():
    mq('submit sleep+3@1x1m -w')
    time.sleep(2)
    Path('wf.py').write_text(wf)
    mq('workflow wf.py .')
    wait()
    assert states() == 'dd'
