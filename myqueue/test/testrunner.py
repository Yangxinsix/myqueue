import os
import shlex
import shutil
import sys
import tempfile
import time
from typing import List, Optional
from pathlib import Path

from myqueue.cli import main
from myqueue.config import initialize_config

LOCAL = True
UPDATE = False


def mq(cmd):
    args = shlex.split(cmd)
    args[1:1] = ['--traceback']
    return main(args)


all_tests = {}


def test(func):
    all_tests[func.__name__] = func
    return func


def find_tests():
    import myqueue.test.mq  # noqa
    import myqueue.test.more  # noqa
    import myqueue.test.docs  # noqa


def states():
    return ''.join(task.state[0] for task in mq('list'))


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
              verbose: bool,
              update_source_code: bool) -> None:

    import myqueue.runner

    global LOCAL, UPDATE
    LOCAL = config_file is None
    UPDATE = update_source_code

    find_tests()

    if LOCAL:
        tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-'))
    else:
        tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-',
                                       dir=str(Path.home())))

    myqueue.runner.use_color = False

    print(f'Running tests in {tmpdir}:')
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

    os.environ['MYQUEUE_TESTING'] = 'yes'

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

        mq('rm -s qrdFTCM . -rq')

        print('OK', file=sys.__stdout__)

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
