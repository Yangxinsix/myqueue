import subprocess
from pathlib import Path
from typing import Optional, List

from myqueue.scheduler import Scheduler
from myqueue.task import Task


class TestScheduler(Scheduler):
    current_scheduler: Optional['TestScheduler'] = None

    def __init__(self, folder: Path):
        self.folder = folder / '.myqueue'
        self.tasks: List[Task] = []
        self.number = 0
        Scheduler.__init__(self)

    def submit(self, task: Task, dry_run: bool = False) -> None:
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

    def kick(self) -> bool:
        for task in self.tasks:
            if task.state == 'queued' and not task.deps:
                break
        else:
            return True

        self.run(task)
        return False

    def run(self, task):
        out = f'{task.cmd.short_name}.{task.id}.out'
        err = f'{task.cmd.short_name}.{task.id}.err'

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            n = task.resources.processes
            cmd = f'MYQUEUE_TEST_NPROCESSES={n} ' + cmd
        cmd = f'cd {task.folder} && {cmd} 2> {err} > {out}'
        activation_script = task.activation_script
        if activation_script:
            cmd = f'. {activation_script} && ' + cmd
        (self.folder / f'test-{task.id}-0').write_text('')
        tmax = task.resources.tmax
        try:
            result = subprocess.run(cmd,
                                    shell=True,
                                    check=not True,
                                    timeout=tmax)
        except subprocess.TimeoutExpired:
            state = 'TIMEOUT'
        else:
            if result.returncode == 0:
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
