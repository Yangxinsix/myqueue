import time
from pathlib import Path

from q2.commands import command

jobstates = ['queued', 'running', 'done',
             'FAILED', 'CANCELED', 'TIMEOUT']

INFINITY = 100

_workflow = {}


class JobError(Exception):
    pass


def T(t):
    """Convert string to seconds."""
    if isinstance(t, str):
        t = {'m': 60, 'h': 3600, 'd': 24 * 3600}[t[-1]] * int(t[:-1])
    return t


def seconds_to_time_string(n):
    n = int(n)
    h, n = divmod(n, 3600)
    m, s = divmod(n, 60)
    if h:
        return '{}:{:02}:{:02}'.format(h, m, s)
    return '{}:{:02}'.format(m, s)


class Job:
    def __init__(self, cmd,
                 args=[],
                 deps=[],
                 cores=None,
                 tmax=None,
                 repeat=0,
                 folder='.',
                 state='UNKNOWN',
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
                assert cores is None and tmax is None
                cores, tmax = resources.split('x')
                cores = [int(c) for c in cores.split(',')]
            cmd = command(cmd, args)

        if isinstance(tmax, str):
            if '+' in tmax:
                assert repeat is None
                tmax, _, repeat = tmax.partition('+')
                if repeat:
                    repeat = int(repeat)
                else:
                    repeat = INFINITY
            tmax = T(tmax)

        self.cmd = cmd
        self.deps = deps
        self.cores = cores or [1]
        self.tmax = tmax or 600
        self.repeat = repeat
        self.folder = '~' / Path(folder).expanduser().absolute().relative_to(
            Path.home())
        self.state = state
        self.id = id
        self.tqueued = tqueued
        self.trunning = trunning
        self.tstop = tstop

        self._done = None
        self.error = error
        self.out_of_memory = False

        if 'jobs' in _workflow:
            _workflow['jobs'].append(self)

    @property
    def name(self):
        return '{}.{}'.format(self.cmd.name, self.id)

    def __str__(self):
        if self.repeat:
            rep = 'x' + str(self.repeat)
        else:
            rep = ''
        t = time.time()
        if self.state == 'queued':
            dt = t - self.tqueued
        elif self.state == 'running':
            dt = t - self.trunning
        else:
            dt = self.tstop - self.trunning
        s = '{} {} {}@{}x{}s{}({}) {} {} {}'.format(
            self.id,
            self.folder,
            self.cmd.name,
            ','.join(str(c) for c in self.cores),
            self.tmax,
            rep,
            ','.join(str(id) for id in self.deps),
            seconds_to_time_string(dt),
            self.state,
            self.error or '')

        return s

    def todict(self):
        return {'cmd': self.cmd.todict(),
                'id': self.id,
                'folder': str(self.folder),
                'deps': self.deps,
                'cores': self.cores,
                'tmax': self.tmax,
                'repeat': self.repeat,
                'state': self.state,
                'tqueued': self.tqueued,
                'trunning': self.trunning,
                'tstop': self.tstop,
                'error': self.error}

    @staticmethod
    def fromdict(dct):
        return Job(cmd=command(**dct.pop('cmd')), **dct)

    def infolder(self, folder):
        return folder == self.folder or folder in self.folder.parents

    def done(self):
        if self._done is None:
            p = (self.folder / '{}.done'.format(self.cmd.name)).expanduser()
            self._done = p.is_file()
        return self._done

    def write_done_file(self):
        p = (self.folder / '{}.done'.format(self.cmd.name)).expanduser()
        p.write_text('')

    def remove_empty_output_files(self):
        for ext in ['.out', '.err']:
            path = (self.folder / (self.name + ext)).expanduser()
            if path.is_file() and path.stat().st_size == 0:
                path.unlink()

    def read_error(self):
        path = (self.folder / (self.name + '.err')).expanduser()
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

    def command(self):
        out = '{name}.out'.format(name=self.name)
        err = '{name}.err'.format(name=self.name)

        cmd = 'cd {} && {} 2> {} > {}'.format(self.folder, self.cmd, err, out)

        return cmd
