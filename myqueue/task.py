import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Any, Dict, Union, Optional, Iterator, TYPE_CHECKING

from .commands import command, Command
from .resources import Resources, T

if TYPE_CHECKING:
    from .scheduler import Scheduler

taskstates = ['queued', 'hold', 'running', 'done',
              'FAILED', 'CANCELED', 'TIMEOUT', 'MEMORY']


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
    workflow: bool
        Task is part of a workflow.
    restart: int
        How many times to restart task.
    diskspace: float
        Disk-space used.  See :ref:`max_disk`.
    folder: Path
        Folder where task should run.
    creates: list of str
        Name of files created by task.
    """
    def __init__(self,
                 cmd: Command,
                 resources: Resources,
                 deps: List[Path],
                 workflow: bool,
                 restart: int,
                 diskspace: int,
                 folder: Path,
                 creates: List[str],
                 state: str = '',
                 id: int = 0,
                 error: str = '',
                 memory_usage: int = 0,
                 tqueued: float = 0.0,
                 trunning: float = 0.0,
                 tstop: float = 0.0) -> None:

        self.cmd = cmd
        self.resources = resources
        self.deps = deps
        self.workflow = workflow
        self.restart = restart
        self.diskspace = diskspace
        self.folder = folder
        self.creates = creates

        self.state = state
        self.id = id
        self.error = error

        # Timing:
        self.tqueued = tqueued
        self.trunning = trunning
        self.tstop = tstop

        self.memory_usage = memory_usage

        self.dname = folder / cmd.name
        self.dtasks: List[Task] = []
        self.activation_script: Optional[Path] = None
        self._done: Optional[bool] = None

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

    def words(self) -> List[str]:
        t = time.time()
        age = t - self.tqueued
        dt = self.running_time(t)

        if self.deps:
            deps = f'({len(self.deps)})'
        else:
            deps = ''

        return [str(self.id),
                str(self.folder) + '/',
                self.cmd.name,
                str(self.resources) + deps +
                ('*' if self.workflow else '') +
                (f'R{self.restart}' if self.restart else '') +
                ('D' if self.diskspace else ''),
                seconds_to_time_string(age),
                self.state,
                seconds_to_time_string(dt),
                self.error]

    def __str__(self) -> str:
        return ' '.join(self.words())

    def __repr__(self) -> str:
        return str(self.dname)
        dct = self.todict()
        return f'Task({dct!r})'

    def order(self, column: str) -> Union[int, str, Path, float]:
        """ifnraste"""
        if column == 'i':
            return self.id
        if column == 'f':
            return self.folder
        if column == 'n':
            return self.name
        if column == 'r':
            return self.resources.cores * self.resources.tmax
        if column == 'a':
            return self.tqueued
        if column == 's':
            return self.state
        if column == 't':
            return self.running_time()
        if column == 'e':
            return self.error
        raise ValueError(f'Unknown column: {column}!  '
                         'Mus be one of i, f, n, r, a, s, t or e')

    def todict(self, root: Path = None) -> Dict[str, Any]:
        folder = self.folder
        deps = self.deps
        if root:
            folder = folder.relative_to(root)
            deps = [dep.relative_to(root) for dep in self.deps]
        return {
            'id': self.id,
            'folder': str(folder),
            'cmd': self.cmd.todict(),
            'state': self.state,
            'resources': self.resources.todict(),
            'restart': self.restart,
            'deps': [str(dep) for dep in deps],
            'workflow': self.workflow,
            'diskspace': self.diskspace,
            'creates': self.creates,
            'tqueued': self.tqueued,
            'trunning': self.trunning,
            'tstop': self.tstop,
            'error': self.error}

    def tocsv(self,
              fd=sys.stdout,
              write_header: bool = False) -> None:
        if write_header:
            print('# id,folder,cmd,resources,state,restart,workflow,'
                  'diskspace,deps,creates,tqueued,trunning,tstop,error',
                  file=fd)
        t1, t2, t3 = (datetime.fromtimestamp(t).strftime('"%Y-%m-%d %H:%M:%S"')
                      for t in [self.tqueued, self.trunning, self.tstop])
        deps = ','.join(str(dep) for dep in self.deps)
        creates = ','.join(self.creates)
        print(f'{self.id},'
              f'"{self.folder}",'
              f'"{self.cmd.name}",'
              f'{self.resources},'
              f'{self.state},'
              f'{self.restart},'
              f'{int(self.workflow)},'
              f'{self.diskspace},'
              f'"{deps}",'
              f'"{creates}",'
              f'{t1},{t2},{t3},'
              f'"{self.error}",'
              f'{self.memory_usage}',
              file=fd)

    @staticmethod
    def fromcsv(row: List[str]) -> 'Task':
        (id, folder, name, resources, state, restart, workflow, diskspace,
         deps, creates, t1, t2, t3, error) = row[:14]
        memory_usage = 0 if len(row) == 14 else int(row[14])
        return Task(command(name),
                    Resources.from_string(resources),
                    [Path(dep) for dep in deps.split(',')],
                    bool(workflow),
                    int(restart),
                    int(diskspace),
                    Path(folder),
                    creates.split(','),
                    state,
                    int(id),
                    error,
                    memory_usage,
                    *(datetime.strptime(t, '%Y-%m-%d %H:%M:%S').timestamp()
                      for t in (t1, t2, t3)))

    @staticmethod
    def fromdict(dct: Dict[str, Any], root: Path) -> 'Task':
        dct = dct.copy()

        # Backwards compatibility with version 2:
        if 'restart' not in dct:
            dct['restart'] = 0
        else:
            dct['restart'] = int(dct['restart'])
        if 'diskspace' not in dct:
            dct['diskspace'] = 0

        # Backwards compatibility with version 3:
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

        return Task(cmd=command(**dct.pop('cmd')),
                    resources=Resources(**dct.pop('resources')),
                    folder=folder,
                    deps=deps,
                    **dct)

    def infolder(self, folder: Path, recursive: bool) -> bool:
        return folder == self.folder or (recursive and
                                         folder in self.folder.parents)

    def is_done(self) -> bool:
        if self._done is None:
            if self.creates:
                for pattern in self.creates:
                    if not any(self.folder.glob(pattern)):
                        self._done = False
                        break
                else:
                    self._done = True
            else:
                self._done = (self.folder / f'{self.cmd.fname}.done').is_file()
        return self._done

    def has_failed(self) -> bool:
        return (self.folder / f'{self.cmd.fname}.FAILED').is_file()

    def skip(self) -> bool:
        return (self.folder / f'{self.cmd.fname}.SKIP').is_file()

    def write_done_file(self) -> None:
        if self.workflow and len(self.creates) == 0 and self.folder.is_dir():
            p = self.folder / f'{self.cmd.fname}.done'
            p.write_text('')

    def write_failed_file(self) -> None:
        if self.workflow and self.folder.is_dir():
            p = self.folder / f'{self.cmd.fname}.FAILED'
            p.write_text('')

    def remove_failed_file(self) -> None:
        p = self.folder / f'{self.cmd.fname}.FAILED'
        if p.is_file():
            p.unlink()

    def read_error(self, scheduler: 'Scheduler') -> bool:
        """Check error message.

        Return True if out of memory.
        """
        self.error = '-'  # mark as already read

        path = scheduler.error_file(self)

        try:
            lines = path.read_text().splitlines()
        except (FileNotFoundError, UnicodeDecodeError):
            return False

        for line in lines[::-1]:
            ll = line.lower()
            if any(x in ll for x in ['error:', 'memoryerror', 'malloc',
                                     'out of memory']):
                self.error = line
                if line.endswith('memory limit at some point.'):
                    return True
                if 'malloc' in line:
                    return True
                if line.startswith('MemoryError'):
                    return True
                if 'oom-kill' in line:
                    return True
                if line.endswith('out of memory'):
                    return True
                return False

        if lines:
            self.error = lines[-1]
        return False

    def ideps(self, map: Dict[Path, 'Task']) -> Iterator['Task']:
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
        from .queue import Queue
        with Queue(verbosity, dry_run=dry_run) as queue:
            queue.submit([self])

    def cancel_dependents(self, tasks: List['Task'], t: float = 0.0) -> None:
        """Cancel dependents."""
        for tsk in tasks:
            if self.dname in tsk.deps and self is not tsk:
                tsk.state = 'CANCELED'
                tsk.tstop = t
                tsk.cancel_dependents(tasks, t)


def task(cmd: str,
         resources: str = '',
         args: List[str] = [],
         name: str = '',
         deps: Union[str, List[str], Task, List[Task]] = '',
         cores: int = 1,
         nodename: str = '',
         processes: int = 0,
         tmax: str = '10m',
         folder: str = '',
         workflow: bool = False,
         restart: int = 0,
         diskspace: float = 0.0,
         creates: List[str] = []) -> Task:
    """Create a Task object.

    ::

        task = task('abc.py')

    Parameters
    ----------
    cmd: str
        Command to be run.
    resources: str
        Resources::

            'cores[:nodename][:processes]:tmax'

        Examples: '48:1d', '32:1h', '8:xeon8:1:30m'.  Can not be used
        togeter with any of "cores", "nodename", "processes" and "tmax".
    args: list of str
        Command-line arguments or function arguments.
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
    folder: str
        Folder where task should run (default is current folder).
    workflow: bool
        Task is part of a workflow.
    restart: int
        How many times to restart task.
    diskspace: float
        Diskspace used.  See :ref:`max_disk`.
    creates: list of str
        Name of files created by task.

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
        c, r = cmd.rsplit('@', 1)
        if r[0].isdigit():
            cmd = c
            resources = r

    if resources:
        res = Resources.from_string(resources)
    else:
        res = Resources(cores, nodename, processes, T(tmax))

    return Task(command(cmd, args, name=name),
                res,
                dpaths,
                workflow,
                restart,
                int(diskspace),
                path,
                creates)


def seconds_to_time_string(n: float) -> str:
    n = int(n)
    d, n = divmod(n, 24 * 3600)
    h, n = divmod(n, 3600)
    m, s = divmod(n, 60)
    if d:
        return f'{d}:{h:02}:{m:02}:{s:02}'
    if h:
        return f'{h}:{m:02}:{s:02}'
    return f'{m}:{s:02}'
