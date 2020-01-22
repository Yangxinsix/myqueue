import os
import shlex
import time
from pathlib import Path
from typing import List, Set

import pytest

from myqueue.cli import _main
from myqueue.config import initialize_config
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.task import Task, taskstates


@pytest.fixture(scope='function')
def mq(tmpdir):
    dir = os.getcwd()
    os.chdir(tmpdir)
    yield MQ(Path(tmpdir))
    os.chdir(dir)


class MQ:
    def __init__(self, dir):
        mqdir = dir / '.myqueue'
        mqdir.mkdir()
        txt = "config = {'scheduler': 'test'}\n"
        (mqdir / 'config.py').write_text(txt)
        initialize_config(dir)
        os.environ['MYQUEUE_TESTING'] = 'yes'

    def __call__(self, cmd):
        args = shlex.split(cmd)
        if args[0][0] != '-' and args[0] != 'help':
            args[1:1] = ['--traceback']
        error = _main(args)
        assert error == 0

    def states(self) -> str:
        return ''.join(task.state[0] for task in mqlist())

    def wait(self) -> None:
        LOCAL = True
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

