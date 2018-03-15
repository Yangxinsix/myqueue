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


class Job:
    def __init__(self, cmd,
                 args=[],
                 deps=[],
                 cores=None,
                 time=None,
                 repeat=0,
                 folder='.',
                 state='UNKNOWN',
                 tstart=None,
                 error='',
                 id=None):
        """Description of a job.

        ::

            task_A1_A2@C1,C2,C3xTxR

        """
        if isinstance(cmd, str):
            cmd, _, resources = cmd.partition('@')
            if resources:
                assert cores is None and time is None
                cores, time = resources.split('x')
                cores = [int(c) for c in cores.split(',')]
            cmd = command(cmd, args)

        if isinstance(time, str):
            if '+' in time:
                assert repeat is None
                time, _, repeat = time.partition('+')
                if repeat:
                    repeat = int(repeat)
                else:
                    repeat = INFINITY
            time = T(time)

        self.cmd = cmd
        self.deps = deps
        self.cores = cores or [1]
        self.time = time or 600
        self.repeat = repeat
        self.folder = '~' / Path(folder).expanduser().absolute().relative_to(
            Path.home())
        self.state = state
        self.id = id
        self.tstart = tstart

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
            if self.repeat == INFINITY:
                rep = '+'
            else:
                rep = '+' + str(self.repeat)
        else:
            rep = ''
        s = '{} {} {}@{}x{}s{}({}) {} {} {}'.format(
            self.id,
            self.folder,
            self.cmd.name,
            ','.join(str(c) for c in self.cores),
            self.time,
            rep,
            ','.join(str(id) for id in self.deps),
            self.state,
            self.tstart, self.error)

        return s

    def todict(self):
        return {'cmd': self.cmd.todict(),
                'id': self.id,
                'folder': str(self.folder),
                'deps': self.deps,
                'cores': self.cores,
                'time': self.time,
                'repeat': self.repeat,
                'state': self.state,
                'tstart': self.tstart,
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
        print(path)
        try:
            lines = path.read_text().splitlines()
        except FileNotFoundError:
            return
        print(lines)
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
