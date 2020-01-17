import json
import os
import subprocess
import sys
from pathlib import Path

from .config import config, initialize_config
from .scheduler import Scheduler
from .task import Task


class TestScheduler(Scheduler):
    def __init__(self):
        self.tasks = []
        self.number = None
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

    def update(self, id: int, state: str) -> None:
        if not state.isalpha():
            if state == '0':
                state = 'done'
            else:
                state = 'FAILED'

        n = {'running': 0,
             'done': 1,
             'FAILED': 2,
             'TIMEOUT': 3}[state]

        self.fname.with_name('local-{}-{}'.format(id, n)).write_text('')

        self._read()
        for task in self.tasks:
            if task.id == id:
                break
        else:
            raise ValueError('No such task: {id}, {state}'
                             .format(id=id, state=state))

        if state == 'done':
            tasks = []
            for j in self.tasks:
                if j is not task:
                    if task.dname in j.deps:
                        j.deps.remove(task.dname)
                    tasks.append(j)
            self.tasks = tasks
        elif state == 'running':
            task.state = 'running'
        else:
            assert state in ['FAILED', 'TIMEOUT'], state
            task.state = 'CANCELED'
            task.cancel_dependents(self.tasks, 0)
            self.tasks = [task for task in self.tasks
                          if task.state != 'CANCELED']

        self._kick()
        self._write()

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
            cmd = mpiexec + cmd.replace('python3',
                                        config.get('parallel_python',
                                                   'python3'))
        else:
            cmd = 'MPLBACKEND=Agg ' + cmd
        cmd = f'cd {task.folder} && {cmd} 2> {err} > {out}'
        tmax = task.resources.tmax
        cmd = (f'({cmd} ; echo $?)& p1=$!; '
               f'(sleep {tmax}; kill $p1 > /dev/null 2>&1; echo TIMEOUT)& '
               'p2=$!; wait $p1; '
               'if [ $? -eq 0 ]; then kill $p2 > /dev/null 2>&1; fi')
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0
        self.update(p.out)
