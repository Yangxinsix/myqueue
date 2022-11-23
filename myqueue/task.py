from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator
from warnings import warn

from myqueue.commands import Command, create_command
from myqueue.errors import parse_stderr
from myqueue.resources import Resources
from myqueue.states import State

if TYPE_CHECKING:
    from myqueue.schedulers import Scheduler

UNSPECIFIED = 'hydelifytskibadut'


class Task:
    """Task object.

    Parameters
    ----------

    cmd: :class:`myqueue.commands.Command`
        Command to be run.
    resources: Resources
        Combination of number of cores, nodename, number of processes
        and maximum time.
    deps: list of Path objects
        Dependencies.
    restart: int
        How many times to restart task.
    workflow: bool
        Task is part of a workflow.
    folder: Path
        Folder where task should run.
    creates: list of str
        Name of files created by task.
    """

    def __init__(self,
                 cmd: Command,
                 *,
                 resources: Resources,
                 deps: list[Path],
                 restart: int,
                 workflow: bool,
                 folder: Path,
                 creates: list[str],
                 notifications: str = '',
                 state: State = State.undefined,
                 id: int = 0,
                 error: str = '',
                 tqueued: float = 0.0,
                 trunning: float = 0.0,
                 tstop: float = 0.0,
                 user: str = ''):

        self.cmd = cmd
        self.resources = resources
        self.deps = deps
        self.restart = restart
        self.workflow = workflow
        self.folder = folder
        self.notifications = notifications
        self.creates = creates

        assert isinstance(state, State), state
        self.state = state
        self.id = id
        self.error = error

        # Timing:
        self.tqueued = tqueued
        self.trunning = trunning
        self.tstop = tstop

        self.user = user or os.environ.get('USER', 'root')

        self.dname = folder / cmd.name
        self.dtasks: list[Task] = []
        self._done: bool | None = None
        self.result = UNSPECIFIED

    @property
    def name(self) -> str:
        return f'{self.cmd.name}.{self.id}'

    def running_time(self, t: float = None) -> float:
        if self.state in ['CANCELED', 'queued', 'hold']:
            dt = 0.0
        elif self.state == 'running':
            t = t or time.time()
            dt = t - self.trunning
        else:
            dt = self.tstop - self.trunning
        return dt

    def words(self) -> list[str]:
        t = time.time()
        age = t - self.tqueued
        dt = self.running_time(t)

        info = []
        if self.restart:
            info.append(f'*{self.restart}')
        if self.deps:
            info.append(f'd{len(self.deps)}')
        if self.cmd.args:
            info.append(f'+{len(self.cmd.args)}')
        if self.notifications:
            info.append(self.notifications)

        return [str(self.id),
                str(self.folder) + '/',
                self.cmd.name.split('+', 1)[0],
                ' '.join(self.cmd.args),
                ','.join(info),
                str(self.resources),
                seconds_to_time_string(age),
                self.state.name,
                seconds_to_time_string(dt),
                self.error]

    def __str__(self) -> str:
        return ' '.join(self.words())

    def __repr__(self) -> str:
        return f'Task({self.cmd.name})'

    def order_key(self, column: str) -> Any:
        """ifnAraste"""
        if column == 'i':
            return self.id
        if column == 'f':
            return self.folder
        if column == 'n':
            return self.name
        if column == 'A':
            return len(self.cmd.args)
        if column == 'r':
            return self.resources.cores * self.resources.tmax
        if column == 'a':
            return self.tqueued
        if column == 's':
            return self.state.name
        if column == 't':
            return self.running_time()
        if column == 'e':
            return self.error
        raise ValueError(f'Unknown column: {column}!  '
                         'Must be one of i, f, n, a, I, r, A, s, t or e')

    def todict(self, root: Path = None) -> dict[str, Any]:
        folder = self.folder
        deps = self.deps
        if root:
            folder = folder.relative_to(root)
            deps = [dep.relative_to(root) for dep in self.deps]
        return {
            'id': self.id,
            'folder': str(folder),
            'cmd': self.cmd.todict(),
            'state': self.state.name,
            'resources': self.resources.todict(),
            'restart': self.restart,
            'workflow': self.workflow,
            'deps': [str(dep) for dep in deps],
            'notifications': self.notifications,
            'creates': self.creates,
            'tqueued': self.tqueued,
            'trunning': self.trunning,
            'tstop': self.tstop,
            'error': self.error,
            'user': self.user}

    def to_sql(self,
               root: Path) -> tuple[int, str, str, str, str,
                                    str, int, bool, str, float,
                                    str, str, float, float, float,
                                    str, str]:
        folder = str(self.folder.relative_to(root))
        if folder == '.':
            folder = './'
        else:
            folder = f'./{folder}/'
        return (self.id,
                folder,
                self.state.name[0],
                # str(self.dname.relative_to(root)),
                self.dname.name,
                json.dumps(self.cmd.todict()),
                json.dumps(self.resources.todict()),
                self.restart,
                self.workflow,
                ','.join(str(dep.relative_to(root)) for dep in self.deps),
                self.resources.weight,
                self.notifications,
                ','.join(self.creates),
                self.tqueued,
                self.trunning,
                self.tstop,
                self.error,
                self.user)

    @staticmethod
    def from_sql_row(row: tuple, root: Path) -> Task:
        (id, folder, state, name, cmd,
         resources, restart, workflow, deps, weight,
         notifications, creates, tqueued, trunning, tstop,
         error, user) = row
        resources = Resources(**json.loads(resources))
        assert resources.weight == weight
        return Task(id=id,
                    folder=root / folder,
                    state=State(state),
                    cmd=create_command(**json.loads(cmd)),
                    resources=resources,
                    restart=restart,
                    workflow=bool(workflow),
                    deps=[] if not deps else [root / dep
                                              for dep in deps.split(',')],
                    notifications=notifications,
                    creates=[] if not creates else creates.split(','),
                    tqueued=tqueued,
                    trunning=trunning,
                    tstop=tstop,
                    error=error,
                    user=user)

    @staticmethod
    def fromdict(dct: dict[str, Any], root: Path) -> Task:
        dct = dct.copy()

        # Backwards compatibility with version 2:
        if 'restart' not in dct:
            dct['restart'] = 0
        else:
            dct['restart'] = int(dct['restart'])

        dct.pop('diskspace', None)

        # Backwards compatibility:
        if 'creates' not in dct:
            dct['creates'] = []

        f = dct.pop('folder')
        if f.startswith('/'):
            # Backwards compatibility with version 5:
            folder = Path(f)
            deps = [Path(dep) for dep in dct.pop('deps')]
        else:
            folder = root / f
            deps = [root / dep for dep in dct.pop('deps')]

        id = int(dct.pop('id'))

        return Task(cmd=create_command(**dct.pop('cmd')),
                    resources=Resources(**dct.pop('resources')),
                    state=State[dct.pop('state')],
                    folder=folder,
                    deps=deps,
                    notifications=dct.pop('notifications', ''),
                    id=id,
                    **dct)

    def infolder(self, folder: Path, recursive: bool) -> bool:
        """Check if task runs inside a folder tree."""
        return folder == self.folder or (recursive and
                                         folder in self.folder.parents)

    def check_creates_files(self) -> bool:
        """Check if all files have been created."""
        if self.creates:
            for pattern in self.creates:
                if not any(self.folder.glob(pattern)):
                    return False
            return True
        return False

    def read_error_and_check_for_oom(self, scheduler: Scheduler) -> bool:
        """Check error message.

        Return True if out of memory.
        """
        self.error = '-'  # mark as already read

        path = scheduler.error_file(self)

        try:
            text = path.read_text()
        except (FileNotFoundError, UnicodeDecodeError):
            return False

        self.error, oom = parse_stderr(text)
        return oom

    def ideps(self, map: dict[Path, Task]) -> Iterator[Task]:
        """Yield task and its dependencies."""
        yield self
        for dname in self.deps:
            yield from map[dname].ideps(map)

    def submit(self, verbosity: int = 1, dry_run: bool = False) -> None:
        """Submit task.

        Parameters
        ----------

        verbosity: int
            Must be 0, 1 or 2.
        dry_run: bool
            Don't actually submit the task.
        """
        from myqueue.config import Configuration
        from myqueue.queue import Queue
        from myqueue.submitting import submit
        config = Configuration.read()
        with Queue(config, dry_run=dry_run) as queue:
            submit(queue, [self], verbosity=verbosity)

    def run(self) -> None:
        self.result = self.cmd.run()


def create_task(cmd: str,
                args: list[str] = [],
                *,
                resources: str = '',
                workflow: bool = False,
                name: str = '',
                deps: str | list[str] | Task | list[Task] = '',
                cores: int = 0,
                nodename: str = '',
                processes: int = 0,
                tmax: str = '',
                weight: float = -1.0,
                folder: str = '',
                restart: int = 0,
                creates: list[str] = []) -> Task:
    """Create a Task object.

    ::

        task = task('abc.py')

    Parameters
    ----------
    cmd: str
        Command to be run.
    args: list of str
        Command-line arguments or function arguments.
    resources: str
        Resources::

            'cores[:nodename][:processes]:tmax'

        Examples: '48:1d', '32:1h', '8:xeon8:1:30m'.  Can not be used
        togeter with any of "cores", "nodename", "processes" and "tmax".
    name: str
        Name to use for task.  Default is <cmd>[+<arg1>[_<arg2>[_<arg3>]...]].
    deps: str, list of str, Task object  or list of Task objects
        Dependencies.  Examples: "task1,task2", "['task1', 'task2']".
    cores: int
        Number of cores (default is 1).
    nodename: str
        Name of node.
    processes: int
        Number of processes to start (default is one for each core).
    tmax: str
        Maximum time for task.  Examples: "40s", "30m", "20h" and "2d".
    workflow: bool
        Task is part of a workflow.
    folder: str
        Folder where task should run (default is current folder).
    restart: int
        How many times to restart task.
    weight: float
        Weight of task.  See :ref:`task_weight`.
    creates: list of str
        Name of files created by task
        (can be both full filenames or patterns matching filenames).

    Returns
    -------
    Task
        Object representing the task.
    """

    path = Path(folder).absolute()

    dpaths = []
    if deps:
        if isinstance(deps, str):
            deps = deps.split(',')
        elif isinstance(deps, Task):
            deps = [deps]
        for dep in deps:
            if isinstance(dep, str):
                p = path / dep
                if '..' in p.parts:
                    p = p.parent.resolve() / p.name
                dpaths.append(p)
            else:
                dpaths.append(dep.dname)

    if '@' in cmd:
        # Old way of specifying resources:
        c, r = cmd.rsplit('@', 1)
        if r[0].isdigit():
            cmd = c
            resources = r
            warn(f'Please use resources={r!r} instead of deprecated '
                 f'...@{r} syntax!')

    command = create_command(cmd, args, name=name)

    res = Resources.from_args_and_command(
        cores, nodename, processes, tmax, weight, resources, command, path)

    return Task(command,
                resources=res,
                deps=dpaths,
                restart=restart,
                workflow=workflow,
                folder=path,
                creates=creates)


task = create_task


def seconds_to_time_string(n: float) -> str:
    """Convert number of seconds to string.

    >>> seconds_to_time_string(10)
    '0:10'
    >>> seconds_to_time_string(3601)
    '1:00:01'
    >>> seconds_to_time_string(24 * 3600)
    '1:00:00:00'
    """
    n = int(n)
    d, n = divmod(n, 24 * 3600)
    h, n = divmod(n, 3600)
    m, s = divmod(n, 60)
    if d:
        return f'{d}:{h:02}:{m:02}:{s:02}'
    if h:
        return f'{h}:{m:02}:{s:02}'
    return f'{m}:{s:02}'
