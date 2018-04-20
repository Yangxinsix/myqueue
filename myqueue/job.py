import time
from pathlib import Path

from myqueue.commands import command

jobstates = ['queued', 'running', 'done',
             'FAILED', 'CANCELED', 'TIMEOUT']


def T(t: str) -> int:
    """Convert string to seconds."""
    return {'s': 1,
            'm': 60,
            'h': 3600,
            'd': 24 * 3600}[t[-1]] * int(t[:-1])


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


class Job:
    def __init__(self, cmd,
                 args=[],
                 deps=[],
                 cores=None,
                 processes=None,
                 tmax=None,
                 repeat=None,
                 folder='.',
                 state='UNKNOWN',
                 workflow=False,
                 tqueued=None,
                 trunning=None,
                 tstop=None,
                 error=None,
                 id=None):
        """Description of a job.

        ::

            task_A1_A2@C1,C2,C3xTxR

        """
        if isinstance(cmd, str):
            cmd, _, resources = cmd.partition('@')
            if resources:
                assert cores is None and tmax is None and processes is None
                cores, tmax = resources.split('x', 1)
                if ':' in cores:
                    cores, processes = cores.split(':')
                else:
                    processes = cores
                cores = int(cores)
                processes = int(processes)
            cmd = command(cmd, args)

        if isinstance(tmax, str):
            if 'x' in tmax:
                assert repeat is None
                tmax, _, repeat = tmax.partition('x')
                repeat = int(repeat) - 1
            tmax = T(tmax)

        self.cmd = cmd
        self.cores = cores or 1
        self.processes = processes or self.cores
        self.tmax = tmax or 600
        self.repeat = repeat or 0
        self.folder = Path(folder).expanduser().absolute()

        self.deps = []
        for dep in deps:
            if isinstance(dep, str):
                if dep[0] == '/':
                    dep = Path(dep)
                else:
                    dep = self.folder / dep
            self.deps.append(dep)

        self.state = state
        self.workflow = workflow
        self.id = id
        self.tqueued = tqueued
        self.trunning = trunning
        self.tstop = tstop

        self.dname = self.folder / cmd.name

        self._done = None
        self.error = error
        self.out_of_memory = False

    @property
    def name(self):
        return '{}.{}'.format(self.cmd.name, self.id)

    def words(self):
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
        return 'Job({!r}, {})'.format(
            dct.pop('cmd')['cmd'],
            ', '.join('{}={!r}'.format(k, v) for k, v in dct.items()))

    def todict(self):
        deps = []
        for dep in self.deps:
            if isinstance(dep, Job):
                dep = dep.dname
            deps.append(str(dep))
        return {'cmd': self.cmd.todict(),
                'id': self.id,
                'folder': str(self.folder),
                'deps': deps,
                'cores': self.cores,
                'processes': self.processes,
                'tmax': self.tmax,
                'repeat': self.repeat,
                'workflow': self.workflow,
                'state': self.state,
                'tqueued': self.tqueued,
                'trunning': self.trunning,
                'tstop': self.tstop,
                'error': self.error}

    @staticmethod
    def fromdict(dct):
        return Job(cmd=command(**dct.pop('cmd')), **dct)

    def infolder(self, folder, recursive):
        return folder == self.folder or (recursive and
                                         folder in self.folder.parents)

    def done(self):
        if self._done is None:
            p = self.folder / '{}.done'.format(self.cmd.name)
            self._done = p.is_file()
        return self._done

    def write_done_file(self):
        p = self.folder / '{}.done'.format(self.cmd.name)
        p.write_text('')

    def remove_empty_output_files(self):
        for ext in ['.out', '.err']:
            path = self.folder / (self.name + ext)
            if path.is_file() and path.stat().st_size == 0:
                path.unlink()

    def read_error(self):
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
