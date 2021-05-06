import os
import shlex
from pathlib import Path
from typing import List, Set

import pytest  # type: ignore

from myqueue.cli import _main
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.task import Task
from myqueue.states import State


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
        os.environ['MYQUEUE_TESTING'] = 'yes'

    def __call__(self, cmd: str, error: int = 0) -> None:
        args = shlex.split(cmd)
        if args and args[0][0] != '-' and args[0] != 'help':
            args[1:1] = ['--traceback']
        print(f'$ mq {cmd}')
        for i, arg in enumerate(args):
            if '*' in arg:
                args[i:i + 1] = sorted([str(p) for p in Path().glob(arg)])
                break
        err = _main(args)
        assert err == error

    def states(self) -> str:
        return ''.join(task.state.value for task in mqlist())

    def wait(self) -> None:
        while True:
            done = self.scheduler.kick()
            if done:
                break


def mqlist(states: Set[State] = None) -> List[Task]:
    states = states if states is not None else set(State)
    with Queue(verbosity=0) as q:
        q._read()
        return Selection(states=states,
                         folders=[Path().absolute()]).select(q.tasks)
