import os
import shlex
from pathlib import Path
from typing import List, Set

import pytest

from myqueue.cli import _main
from myqueue.config import initialize_config
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.task import Task, taskstates
from myqueue.test.scheduler import TestScheduler


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
        initialize_config(dir, force=True)
        self.scheduler = TestScheduler(dir)
        TestScheduler.current_scheduler = self.scheduler
        os.environ['MYQUEUE_TESTING'] = 'yes'

    def __call__(self, cmd):
        args = shlex.split(cmd)
        if args[0][0] != '-' and args[0] != 'help':
            args[1:1] = ['--traceback']
        error = _main(args, is_test=True)
        assert error == 0

    def states(self) -> str:
        return ''.join(task.state[0] for task in mqlist())

    def wait(self) -> None:
        while True:
            done = self.scheduler.kick()
            if done:
                break


def mqlist(states: Set[str] = None) -> List[Task]:
    states = states or set(taskstates)
    with Queue(verbosity=0) as q:
        q._read()
        return Selection(states=states,
                         folders=[Path().absolute()]).select(q.tasks)

