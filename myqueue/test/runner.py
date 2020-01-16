import os
import shlex
import shutil
import sys
import tempfile
import time
from pathlib import Path
from textwrap import wrap
from typing import List, Optional, Callable, Set
from unittest import SkipTest

from myqueue.cli import _main
from myqueue.config import initialize_config
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.task import Task, taskstates

LOCAL = True
UPDATE = False


def mq(cmd: str) -> None:
    args = shlex.split(cmd)
    if args[0][0] != '-' and args[0] != 'help':
        args[1:1] = ['--traceback']
    error = _main(args)
    assert error == 0


all_tests = {}


def test(func: Callable[[], None]) -> Callable[[], None]:
    """Decorator for test functions."""
    all_tests[func.__name__] = func
    return func


def find_tests() -> None:
    import myqueue.test.mq  # noqa
    import myqueue.test.more  # noqa
    import myqueue.test.docs  # noqa


def mqlist(states: Set[str] = None) -> List[Task]:
    states = states or set(taskstates)
    with Queue(verbosity=0) as q:
        q._read()
        return Selection(states=states,
                         folders=[Path().absolute()]).select(q.tasks)


def states() -> str:
    return ''.join(task.state[0] for task in mqlist())


def wait() -> None:
    t0 = time.time()
    timeout = 10.0 if LOCAL else 1300.0
    sleep = 0.1 if LOCAL else 3.0
    while True:
        if len(mqlist({'queued', 'running'})) == 0:
            return
        time.sleep(sleep)
        if time.time() - t0 > timeout:
            raise TimeoutError


def run_tests(tests: List[str],
              config_file: Optional[Path],
              exclude: List[str],
              verbose: bool,
              update_source_code: bool) -> None:

    import myqueue.queue

    global LOCAL, UPDATE
    LOCAL = config_file is None
    UPDATE = update_source_code

    find_tests()

    if LOCAL:
        tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-'))
    else:
        tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-',
                                       dir=str(Path.home())))

    myqueue.queue.use_color = False

    print(f'Running tests in {tmpdir}:')
    os.chdir(str(tmpdir))

    if not tests:
        tests = list(all_tests)

    (tmpdir / '.myqueue').mkdir()

    if config_file:
        txt = config_file.read_text()
    else:
        txt = 'config = {}\n'.format({'scheduler': 'local'})
        if 'oom' in tests:
            tests.remove('oom')
    (tmpdir / '.myqueue' / 'config.py').write_text(txt)
    initialize_config(tmpdir)

    os.environ['MYQUEUE_TESTING'] = 'yes'

    for test in exclude:
        tests.remove(test)

    if verbose:
        print('\n'.join(wrap(', '.join(tests))))

    if not verbose:
        sys.stdout = open(tmpdir / '.myqueue/stdout.txt', 'w')

    N = 79
    for name in tests:
        if verbose:
            print()
            print('#' * N)
            print(f' Running "{name}" test '.center(N, '#'))
            print('#' * N)
            print()
        else:
            print(name, '...', end=' ', flush=True, file=sys.__stdout__)

        try:
            all_tests[name]()
        except SkipTest:
            print('SKIPPED', file=sys.__stdout__)
        except Exception:
            sys.stdout = sys.__stdout__
            print('FAILED')
            raise
        else:
            print('OK', file=sys.__stdout__)

        mq('rm -s qrdFTCM . -rq')

        for f in tmpdir.glob('*'):
            if f.is_file():
                f.unlink()
            elif f.name != '.myqueue':
                shutil.rmtree(f)

    sys.stdout = sys.__stdout__

    for f in tmpdir.glob('.myqueue/*'):
        f.unlink()

    (tmpdir / '.myqueue').rmdir()
    tmpdir.rmdir()
