"""

module@1,2.3,txt
module:func@1,2.3,txt
~/folder/script.py@a,2.3,txt


"""

from pathlib import Path


jobstates = ['todo', 'queued', 'running', 'done',
             'FAILED', 'CANCELED', 'TIMEOUT']


class JobError(Exception):
    pass


def T(t):
    """Convert string to seconds."""
    if isinstance(t, str):
        t = {'m': 60, 'h': 3600, 'd': 24 * 3600}[t[-1]] * int(t[:-1])
    return t


class Job:
    def __init__(self, name, deps=[], cores=None, time='1m', folder=None,
                 flow=True, state='UNKNOWN', runner='local'):
        name, _, resources = name.partition('@')
        if resources:
            assert cores is None and time is None
            cores, time = resources.split('x')
            cores = int(cores)

        self.module, _, self.function = name.partition(':')
        if self.module.endswith('.py'):
            self.script = self.module
            self.module = None
        else:
            self.script = None

        self.name = name
        self.deps = deps
        self.cores = cores
        self.time = T(time)
        self.folder = folder
        self.flow = flow
        self.runner = runner

        self.uid = str(folder) + ',' + name

        # state is one of:
        # UNKNOWN, todo, queued, running, done, FAILED, TIMEOUT
        self.state = state

        self.jobid = 0

    def __str__(self):
        s = '{}:{}[{}],{},{}{}'.format(
            self.jobid,
            self.uid,
            ','.join(str(id) for id in self.deps),
            self.state,
            self.runner,
            '*' if self.flow else '')
        return s

    def astuple(self):
        return (self.jobid,
                str(self.folder),
                self.name,
                self.deps,
                self.state,
                self.runner,
                self.flow)

    @staticmethod
    def fromtuple(tpl):
        id, folder, name, deps, state, runner, flow = tpl
        job = Job(name,
                  deps=deps,
                  folder=Path(folder),
                  flow=flow,
                  state=state,
                  runner=runner)
        job.id = id
        return job

    def remove_empty_output_files(self):
        for ext in ['.out', '.err']:
            path = self.folder / (self.name + ext)
            if path.is_file() and path.stat().st_size == 0:
                path.unlink()

    def command(self):
        if self.script:
            args = self.script
        elif self.function:
            args = ('-c "import {module}; {module}.{function}()"'
                    .format(module=self.module, function=self.function))
        else:
            args = '-m ' + self.module

        out = '{name}.out'.format(name=self.name)
        err = '{name}.err'.format(name=self.name)

        cmd = f'cd {self.folder} && python3 {args} 2> {err} > {out}'

        return cmd
