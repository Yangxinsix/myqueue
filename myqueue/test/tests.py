import os
import tempfile
import time
from pathlib import Path

from myqueue.cli import main


TIMEOUT = 10.0


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
    while mq('list -s qr -qq'):
        time.sleep(0.1)
        if time.time() - t0 > TIMEOUT:
            raise TimeoutError


def run_tests(tests, timeout):
    global TIMEOUT
    TIMEOUT = timeout
    print('Running tests in', tmpdir)
    os.chdir(str(tmpdir))
    # os.environ['MYQUEUE_HOME'] = str(tmpdir)
    os.environ['MYQUEUE_DEBUG'] = 'yes!'

    if not tests:
        tests = sorted(all_tests)

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
    mq('submit sleep+3@1x1s')
    mq('submit echo+hello -d sleep+3')
    wait()
    mq('resubmit -sT . -R 1x5s')
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
