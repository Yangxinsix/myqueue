from __future__ import annotations
import subprocess

from .task import Task


def run_tasks(tasks: list[Task]) -> None:
    for task in tasks:
        cmd = str(task.cmd)
        print(f'{task.folder}: {cmd}')
        cmd = 'MPLBACKEND=Agg ' + cmd
        cmd = f'cd {task.folder} && {cmd}'
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0


def run(self,
        tasks: list[Task]) -> None:
    """Run tasks locally."""
    self._read()
    dnames = {task.dname for task in tasks}
    self._remove([task for task in self.tasks if task.dname in dnames])
    if self.dry_run:
        for task in tasks:
            print(f'{task.folder}: {task.cmd}')
    else:
        run_tasks(tasks)

