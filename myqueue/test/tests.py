import os
import sys
import tempfile
import time
from typing import List, Optional
from pathlib import Path

from myqueue.cli import main
from myqueue.config import initialize_config


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


def wait() -> None:
    t0 = time.time()
    timeout = 10.0 if LOCAL else 1300.0
    sleep = 0.1 if LOCAL else 3.0
    while mq('list -s qr -qq'):
        time.sleep(sleep)
        if time.time() - t0 > timeout:
            raise TimeoutError


def run_tests(tests: List[str],
              config_file: Optional[Path],
              exclude: List[str],
              verbose: bool) -> None:
    global LOCAL
    LOCAL = config_file is None

    if LOCAL:
        tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-'))
    else:
        tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-',
                                       dir=str(Path.home())))

    print('\nRunning tests in', tmpdir)
    os.chdir(str(tmpdir))

    if not tests:
        tests = list(all_tests)

    (tmpdir / '.myqueue').mkdir()

    if config_file:
        txt = config_file.read_text()
    else:
        txt = 'config = {}\n'.format({'queue': 'local'})
        if 'oom' in tests:
            tests.remove('oom')
    (tmpdir / '.myqueue' / 'config.py').write_text(txt)
    initialize_config(tmpdir)

    os.environ['MYQUEUE_DEBUG'] = 'yes'

    for test in exclude:
        tests.remove(test)

    if not verbose:
        sys.stdout = open(tmpdir / '.myqueue/stdout.txt', 'w')

    N = 79
    for name in tests:
        if verbose:
            print()
            print('#' * N)
            print(' Running "{}" test '.format(name).center(N, '#'))
            print('#' * N)
            print()
        else:
            print(name, '...', end=' ', flush=True, file=sys.__stdout__)

        try:
            all_tests[name]()
        except Exception:
            sys.stdout = sys.__stdout__
            print('FAILED')
            raise
        else:
            print('OK', file=sys.__stdout__)

        mq('rm -s qrdFTCM . -r')

        for f in tmpdir.glob('*'):
            if f.is_file():
                f.unlink()

    sys.stdout = sys.__stdout__

    for f in tmpdir.glob('.myqueue/*'):
        f.unlink()

    (tmpdir / '.myqueue').rmdir()
    tmpdir.rmdir()


@test
def submit():
    mq('submit time:sleep+2')
    mq('submit echo+hello -d time:sleep+2')
    wait()
    for job in mq('list'):
        assert job.state == 'done'


@test
def fail():
    mq('submit time:sleep+a')
    mq('submit echo+hello -d time:sleep+a')
    mq('submit echo+hello2 -d echo+hello')
    wait()
    assert states() == 'FCC'
    mq('resubmit -sF .')
    wait()
    assert states() == 'CCF'


@test
def fail2():
    mq('submit time:sleep+a --workflow')
    wait()
    assert states() == 'F'
    mq('remove --state F .')
    mq('submit time:sleep+a --workflow')
    wait()
    assert states() == ''


@test
def timeout():
    t = 3 if LOCAL else 120
    mq(f'submit -n zzz sleep@1:1s -- {t}')
    mq('submit echo+hello -d zzz')
    wait()
    mq('resubmit -sT . -R 1:5m')
    wait()
    assert states() == 'Cd'


@test
def timeout2():
    t = 3 if LOCAL else 120
    mq('submit sleep@1:{}s --restart 2 -- {}'.format(t // 3, t))
    mq('submit echo+hello -d sleep+{}'.format(t))
    wait()
    mq('kick')
    wait()
    if states() != 'dd':
        mq('kick')
        wait()
        assert states() == 'dd'


@test
def oom():
    mq('submit myqueue.test:oom --restart 2 -- {}'.format(LOCAL))
    wait()
    assert states() == 'M'
    mq('kick')
    wait()
    assert states() == 'd'


wf = """
from myqueue.task import task
def create_tasks():
    t1 = task('sleep+3')
    return [t1, task('touch+hello', deps=[t1], creates=['hello'])]
"""


@test
def workflow():
    mq('submit sleep+3@1:1m -w')
    time.sleep(2)
    Path('wf.py').write_text(wf)
    mq('workflow wf.py . -t touch+hello')
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


@test
def cancel():
    mq('submit sleep+2')
    mq('submit sleep+999')
    mq('submit echo+hello -d sleep+999')
    mq('rm -n sleep+999 -srq .')
    wait()
    assert states() == 'd'


@test
def check_dependency_order():
    mq('submit myqueue.test:timeout_once -R 1:1s --restart 1')
    mq('submit echo+ok -d myqueue.test:timeout_once --restart 1')
    wait()
    assert states() == 'TC'
    mq('kick')
    wait()
    assert states() == 'dd'
