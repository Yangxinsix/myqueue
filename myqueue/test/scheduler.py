import subprocess
from pathlib import Path

from .scheduler import Scheduler
from .task import Task


class TestScheduler(Scheduler):
    def __init__(self, folder: Path):
        self.folder = folder / '.myqueue'
        self.tasks = []
        self.number = 1
        Scheduler.__init__(self)

    def submit(self, task: Task, activation_script: Path = None,
               dry_run: bool = False) -> None:
        assert not dry_run
        if task.dtasks:
            ids = {t.id for t in self.tasks}
            for t in task.dtasks:
                assert t.id in ids
        self.number += 1
        task.id = self.number
        self.tasks.append(task)

    def cancel(self, task):
        assert task.state == 'queued', task
        for i, j in enumerate(self.tasks):
            if task.id == j.id:
                break
        else:
            return
        del self.tasks[i]

    def hold(self, task):
        assert task.state == 'queued', task
        for i, j in enumerate(self.tasks):
            if task.id == j.id:
                break
        else:
            raise ValueError('No such task!')
        j.state = 'hold'

    def release_hold(self, task):
        assert task.state == 'hold', task
        for i, j in enumerate(self.tasks):
            if task.id == j.id:
                break
        else:
            raise ValueError('No such task!')
        j.state = 'queued'

    def get_ids(self):
        return {task.id for task in self.tasks}

    def kick(self) -> None:
        for task in self.tasks:
            if task.state == 'queued' and not task.deps:
                break
        else:
            return

        self.run(task)

    def run(self, task):
        out = f'{task.cmd.short_name}.{task.id}.out'
        err = f'{task.cmd.short_name}.{task.id}.err'

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 -x MPLBACKEND=Agg '
            mpiexec += f'-np {task.resources.processes} '
            cmd = mpiexec + cmd
        else:
            cmd = 'MPLBACKEND=Agg ' + cmd
        cmd = f'cd {task.folder} && {cmd} 2> {err} > {out}'
        tmax = task.resources.tmax
        cmd = (f'({cmd} ; echo $?)& p1=$!; '
               f'(sleep {tmax}; kill $p1 > /dev/null 2>&1; echo TIMEOUT)& '
               'p2=$!; wait $p1; '
               'if [ $? -eq 0 ]; then kill $p2 > /dev/null 2>&1; fi')

        (self.folder / f'test-{task.id}-0').write_text('')

        result = subprocess.run(cmd,
                                shell=True,
                                check=True,
                                stdout=subprocess.PIPE)
        state = result.stdout.decode().strip()
        if state != 'TIMEOUT':
            if state == '0':
                state = 'done'
            else:
                state = 'FAILED'
        self.update(task, state)

    def update(self, task: Task, state: str) -> None:
        n = {'done': 1,
             'FAILED': 2,
             'TIMEOUT': 3}[state]

        (self.folder / f'test-{task.id}-{n}').write_text('')

        if state == 'done':
            tasks = []
            for j in self.tasks:
                if j is not task:
                    if task.dname in j.deps:
                        j.deps.remove(task.dname)
                    tasks.append(j)
            self.tasks = tasks
        else:
            task.state = 'CANCELED'
            task.cancel_dependents(self.tasks, 0)
            self.tasks = [task for task in self.tasks
                          if task.state != 'CANCELED']
