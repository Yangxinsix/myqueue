import os
import time
from pathlib import Path
from typing import List, Any, Dict, Union, Optional  # noqa

from myqueue.commands import command, Command
from myqueue.config import read_config
from myqueue.resources import Resources, T


taskstates = ['queued', 'hold', 'running', 'done',
              'FAILED', 'CANCELED', 'TIMEOUT', 'MEMORY']


class Task:
    def __init__(self,
                 cmd: Command,
                 resources: Resources,
                 deps: List[Path],
                 workflow: bool,
                 restart: bool,
                 diskspace: int,
                 folder: Path,
                 state: str = '',
                 id: int = 0,
                 error: str = '',
                 tqueued: float = 0.0,
                 trunning: float = 0.0,
                 tstop: float = 0.0) -> None:
        """Description of a task."""

        self.cmd = cmd
        self.resources = resources
        self.deps = deps
        self.workflow = workflow
        self.restart = restart
        self.diskspace = diskspace
        self.folder = folder

        self.state = state
        self.id = id
        self.error = error

        # Timing:
        self.tqueued = tqueued
        self.trunning = trunning
        self.tstop = tstop

        self.dname = folder / cmd.name
        self.dtasks = []  # type: List[Task]

        self._done = None  # type: Optional[bool]

    @property
    def name(self) -> str:
        return '{}.{}'.format(self.cmd.name, self.id)

    def words(self) -> List[str]:
        t = time.time()
        if self.state == 'queued':
            dt = t - self.tqueued
            age = dt
        elif self.state == 'running':
            dt = t - self.trunning
            age = dt
        elif self.state == 'CANCELED':
            dt = self.tstop - self.tqueued
            age = t - self.tstop
        else:
            if self.trunning is None:
                dt = 0
                print('???')
            else:
                dt = self.tstop - self.trunning
            age = t - self.tstop

        if self.deps:
            deps = '({})'.format(len(self.deps))
        else:
            deps = ''

        return [str(self.id),
                str(self.folder),
                self.cmd.name,
                str(self.resources) + deps +
                ('*' if self.workflow else '') +
                ('R' if self.restart else '') +
                ('D' if self.diskspace else ''),
                seconds_to_time_string(age),
                self.state,
                seconds_to_time_string(dt),
                self.error]

    def __str__(self):
        return ' '.join(self.words())

    def __repr__(self):
        return str(self.dname)
        dct = self.todict()
        return 'Task({!r})'.format(dct)

    def todict(self) -> Dict[str, Any]:
        return {'cmd': self.cmd.todict(),
                'id': self.id,
                'folder': str(self.folder),
                'deps': [str(dep) for dep in self.deps],
                'resources': self.resources.todict(),
                'workflow': self.workflow,
                'restart': self.restart,
                'diskspace': self.diskspace,
                'state': self.state,
                'tqueued': self.tqueued,
                'trunning': self.trunning,
                'tstop': self.tstop,
                'error': self.error}

    @staticmethod
    def fromdict(dct: dict) -> 'Task':
        dct = dct.copy()
        if 'restart' not in dct:
            dct['restart'] = False
        if 'diskspace' not in dct:
            dct['diskspace'] = 0
        return Task(cmd=command(**dct.pop('cmd')),
                    resources=Resources(**dct.pop('resources')),
                    folder=Path(dct.pop('folder')),
                    deps=[Path(dep) for dep in dct.pop('deps')],
                    **dct)

    @staticmethod
    def fromolddict(dct: dict) -> 'Task':
        del dct['repeat']
        return Task(cmd=command(**dct.pop('cmd')),
                    resources=Resources(dct.pop('cores'),
                                        '',
                                        dct.pop('processes'),
                                        dct.pop('tmax')),
                    folder=Path(dct.pop('folder')),
                    deps=[Path(dep) for dep in dct.pop('deps')],
                    tqueued=float(dct.pop('tqueued') or 0),
                    trunning=float(dct.pop('trunning') or 0),
                    tstop=float(dct.pop('tstop') or 0),
                    id=int(dct.pop('id')),
                    error=dct.pop('error') or '',
                    **dct)

    def infolder(self, folder: Path, recursive: bool) -> bool:
        return folder == self.folder or (recursive and
                                         folder in self.folder.parents)

    def queue_name(self) -> str:
        if os.environ.get('MYQUEUE_DEBUG', '') == 'local':
            return 'local'
        if self.resources.nodename == 'local':
            return 'local'
        cfg = read_config()
        return cfg.get('queue', 'slurm')

    def is_done(self) -> bool:
        if self._done is None:
            p = self.folder / '{}.done'.format(self.cmd.name)
            self._done = p.is_file()
        return self._done

    def has_failed(self) -> bool:
        p = self.folder / '{}.FAILED'.format(self.cmd.name)
        return p.is_file()

    def skip(self) -> bool:
        p = self.folder / '{}.SKIP'.format(self.cmd.name)
        return p.is_file()

    def write_done_file(self) -> None:
        if self.workflow and self.folder.is_dir():
            p = self.folder / '{}.done'.format(self.cmd.name)
            p.write_text('')

    def write_failed_file(self) -> None:
        if self.workflow and self.folder.is_dir():
            p = self.folder / '{}.FAILED'.format(self.cmd.name)
            p.write_text('')

    def remove_failed_file(self) -> None:
        p = self.folder / '{}.FAILED'.format(self.cmd.name)
        if p.is_file():
            p.unlink()

    def read_error(self) -> bool:
        """Check error message.

        Return True if out of memory.
        """
        self.error = '-'  # mark as already read

        if self.queue_name() == 'pbs':
            path = self.folder / '{}.e{}'.format(self.cmd.name, self.id)
        else:
            path = self.folder / (self.name + '.err')

        try:
            lines = path.read_text().splitlines()
        except FileNotFoundError:
            return False

        for line in lines[::-1]:
            ll = line.lower()
            if any(ll in x for x in ['error:', 'memoryerror', 'malloc']):
                self.error = line
                if line.endswith('memory limit at some point.'):
                    return True
                if 'malloc' in line:
                    return True
                if line.startswith('MemoryError'):
                    return True
                if 'oom-kill' in line:
                    return True
                return False

        if lines:
            self.error = lines[-1]
        return False


def task(cmd: str,
         resources: str = '',
         args: List[str] = [],
         deps: Union[str, List[str], List[Task]] = '',
         cores: int = 1,
         nodename: str = '',
         processes: int = 0,
         tmax: str = '10m',
         folder: str = '',
         workflow: bool = False,
         restart: bool = False,
         diskspace: float = 0.0) -> Task:

    path = Path(folder).absolute()

    dpaths = []
    if deps:
        if isinstance(deps, str):
            deps = deps.split(',')
        for dep in deps:
            if isinstance(dep, str):
                p = path / dep
                if '..' in p.parts:
                    p = p.parent.resolve() / p.name
                dpaths.append(p)
            else:
                dpaths.append(dep.dname)

    if '@' in cmd:
        cmd, resources = cmd.split('@')

    if resources:
        res = Resources.from_string(resources)
    else:
        res = Resources(cores, nodename, processes, T(tmax))

    return Task(command(cmd, args), res, dpaths, workflow, restart,
                int(diskspace), path)


def seconds_to_time_string(n: float) -> str:
    n = int(n)
    d, n = divmod(n, 24 * 3600)
    h, n = divmod(n, 3600)
    m, s = divmod(n, 60)
    if d:
        return '{}:{:02}:{:02}:{:02}'.format(d, h, m, s)
    if h:
        return '{}:{:02}:{:02}'.format(h, m, s)
    return '{}:{:02}'.format(m, s)
