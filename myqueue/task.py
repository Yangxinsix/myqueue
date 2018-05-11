import time
from pathlib import Path
from typing import List, Any, Dict

from myqueue.commands import command, Command
from myqueue.resources import Resources

taskstates = ['queued', 'running', 'done',
              'FAILED', 'CANCELED', 'TIMEOUT']


class Task:
    def __init__(self,
                 cmd: Command,
                 resources: Resources,
                 dpaths: List[Path],
                 workflow: bool,
                 folder: Path,
                 queue: str):
        """Description of a task."""

        self.cmd = cmd
        self.resources = resources
        self.dpaths = dpaths
        self.workflow = workflow
        self.folder = folder
        self.queuename = queue

        self.state = ''
        self.id = 0
        self.error = ''

        # Timing:
        self.tqueued = 0.0
        self.trunning = 0.0
        self.tstop = 0.0

        self.dname = self.folder / cmd.name
        self.dtasks = []  # type: List[Task]

        self._done = None

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

        if self.processes == self.cores:
            cores = self.cores
        else:
            cores = '{}:{}'.format(self.cores, self.processes)

        return [str(self.id),
                str(self.folder),
                self.cmd.name,
                '{}x{}'.format(cores,
                               seconds_to_short_time_string(self.tmax)) +
                deps +
                ('*' if self.workflow else ''),
                seconds_to_time_string(age),
                self.state,
                seconds_to_time_string(dt),
                self.error or '']

    def __str__(self):
        return ' '.join(self.words())

    def __repr__(self):
        dct = self.todict()
        return 'Task({!r})'.format(dct)

    def todict(self) -> Dict[str, Any]:
        deps = []
        for dep in self.deps:
            if isinstance(dep, Task):
                dep = dep.dname
            deps.append(str(dep))
        return {'cmd': self.cmd.todict(),
                'id': self.id,
                'folder': str(self.folder),
                'deps': deps,
                'resources': self.resources.todict(),
                'workflow': self.workflow,
                'queue': self.queuename,
                'state': self.state,
                'tqueued': self.tqueued,
                'trunning': self.trunning,
                'tstop': self.tstop,
                'error': self.error}

    @staticmethod
    def fromdict(dct: dict) -> 'Task':
        return Task(cmd=command(**dct.pop('cmd')),
                    resources=Resources(**dct.pop('resources')),
                    **dct)

    def infolder(self, folder: Path, recursive: bool) -> bool:
        return folder == self.folder or (recursive and
                                         folder in self.folder.parents)

    def done(self) -> bool:
        if self._done is None:
            p = self.folder / '{}.done'.format(self.cmd.name)
            self._done = p.is_file()
        return self._done

    def write_done_file(self) -> None:
        if self.workflow:
            p = self.folder / '{}.done'.format(self.cmd.name)
            p.write_text('')
        p = self.folder / '{}.FAILED'.format(self.cmd.name)
        if p.is_file():
            p.unlink()

    def write_failed_file(self) -> None:
        if self.workflow:
            p = self.folder / '{}.FAILED'.format(self.cmd.name)
            p.write_text('')

    def remove_empty_output_files(self) -> None:
        for ext in ['.out', '.err']:
            path = self.folder / (self.name + ext)
            if path.is_file() and path.stat().st_size == 0:
                path.unlink()

    def read_error(self) -> None:
        path = self.folder / (self.name + '.err')
        try:
            lines = path.read_text().splitlines()
        except FileNotFoundError:
            return
        for line in lines[::-1]:
            if 'error: ' in line.lower():
                self.error = line
                if line.endswith('memory limit at some point.'):
                    self.out_of_memory = True
                return
        self.error = lines[-1]

    def command(self) -> str:
        out = '{name}.out'.format(name=self.name)
        err = '{name}.err'.format(name=self.name)

        cmd = 'cd {} && {} 2> {} > {}'.format(self.folder, self.cmd, err, out)

        return cmd


def task(cmd: str,
         resources: str = '',
         args: List[str] = [],
         deps: str = '',
         cores: int = 0,
         nodename: str = '',
         processes: int = 0,
         tmax: str = '10m',
         folder: str = '',
         workflow: bool = False) -> Task:

    folder = Path(folder).absolute()

    dpaths = []
    if deps:
        for dep in deps.split(','):
            dep = folder / dep
            if '..' in dep.parts:
                dep = dep.parent.resolve() / dep.name
            dpaths.append(dep)

    if '@' in cmd:
        cmd, resources = cmd.split('@')

    if resources:
        resources = Resources.from_string(resources)
    else:
        resources = Resources.from_string(cores, nodename, processes, tmax)

    cmd = command(cmd, args)

    return Task(cmd, resources, dpaths, workflow, folder)


def seconds_to_time_string(n: int) -> str:
    n = int(n)
    d, n = divmod(n, 24 * 3600)
    h, n = divmod(n, 3600)
    m, s = divmod(n, 60)
    if d:
        return '{}:{:02}:{:02}:{:02}'.format(d, h, m, s)
    if h:
        return '{}:{:02}:{:02}'.format(h, m, s)
    return '{}:{:02}'.format(m, s)


def seconds_to_short_time_string(n):
    n = int(n)
    for s, t in [('d', 24 * 3600),
                 ('h', 3600),
                 ('m', 60),
                 ('s', 1)]:
        if n % t == 0:
            return '{}{}'.format(n // t, s)
