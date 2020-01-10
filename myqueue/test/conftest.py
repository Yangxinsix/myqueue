import os
import shlex
import shutil
import sys
import tempfile
import time
from pathlib import Path
from textwrap import wrap
from typing import List, Optional, Callable, Set

import pytest

from myqueue.cli import _main
from myqueue.config import initialize_config
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.task import Task, taskstates

LOCAL = True
UPDATE = False


@pytest.fixture
def mq(tmpdir):
    cd
    yield mq1
    cd


class MQ:
    def __call__(self, cmd):
        args = shlex.split(cmd)
        if args[0][0] != '-' and args[0] != 'help':
            args[1:1] = ['--traceback']
        error = _main(args)
        assert error == 0

    def states(self) -> str:
        return ''.join(task.state[0] for task in mqlist())

    def wait(self) -> None:
        t0 = time.time()
        timeout = 10.0 if LOCAL else 1300.0
        sleep = 0.1 if LOCAL else 3.0
        while True:
            if len(mqlist({'queued', 'running'})) == 0:
                return
            time.sleep(sleep)
            if time.time() - t0 > timeout:
                raise TimeoutError


def mqlist(states: Set[str] = None) -> List[Task]:
    states = states or set(taskstates)
    with Queue(verbosity=0) as q:
        q._read()
        return Selection(states=states,
                         folders=[Path().absolute()]).select(q.tasks)




def run_tests(tests: List[str],
              config_file: Optional[Path],
              exclude: List[str],
              verbose: bool,
              update_source_code: bool) -> None:

    import myqueue.queue

    global LOCAL, UPDATE
    LOCAL = config_file is None
    UPDATE = update_source_code


    if LOCAL:
        tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-'))
    else:
        tmpdir = Path(tempfile.mkdtemp(prefix='myqueue-test-',
                                       dir=str(Path.home())))

    myqueue.queue.use_color = False

    (tmpdir / '.myqueue').mkdir()

    if config_file:
        txt = config_file.read_text()
    else:
        txt = 'config = {}\n'.format({'scheduler': 'local'})
    (tmpdir / '.myqueue' / 'config.py').write_text(txt)
    initialize_config(tmpdir)

    os.environ['MYQUEUE_TESTING'] = 'yes'
