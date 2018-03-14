"""

module@1,2.3,txt
module:func@1,2.3,txt
~/folder/script.py@a,2.3,txt

c2dm.relax:run_1_Cu.12234.err
relax.py_Cu
echo_hello
"""

from pathlib import Path

from q2.commands import command

jobstates = ['queued', 'running',
             'FAILED', 'CANCELED', 'TIMEOUT']

INFINITY = 100


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
                 cores=[1],
                 time='1m',
                 repeat=0,
                 folder='.',
                 flow=True,
                 state='UNKNOWN',
                 runner='local',
                 id=None):
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
        self.cores = cores
        self.time = time
        self.repeat = repeat
        self.folder = '~' / Path(folder).expanduser().absolute().relative_to(
            Path.home())
        self.flow = flow
        self.runner = runner
        self.state = state
        self.id = id

        self._done = None

    @property
    def uid(self):
        return '{}:{}'.format(self.runner, self.id)

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
        s = '{} {} {}@{}x{}s{}({}) {}{}'.format(
            self.uid,
            self.folder,
            self.cmd.name,
            ','.join(str(c) for c in self.cores),
            self.time,
            rep,
            ','.join(str(id) for id in self.deps),
            self.state,
            '*' if self.flow else '')
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
                'runner': self.runner,
                'flow': self.flow}

    @staticmethod
    def fromdict(dct):
        return Job(cmd=command(**dct.pop('cmd')), **dct)

    def infolder(self, folder):
        return folder == self.folder or folder in self.folder.parents

    def done(self):
        if self._done is None:
            p = self.folder / '{}.done'.format(self.cmd.name)
            self._done = p.is_file()
        return self._done

    def remove_empty_output_files(self):
        for ext in ['.out', '.err']:
            path = (self.folder / (self.name + ext)).expanduser()
            if path.is_file() and path.stat().st_size == 0:
                path.unlink()

    def command(self):
        out = '{name}.out'.format(name=self.name)
        err = '{name}.err'.format(name=self.name)

        cmd = 'cd {} && {} 2> {} > {}'.format(self.folder, self.cmd, err, out)

        return cmd
