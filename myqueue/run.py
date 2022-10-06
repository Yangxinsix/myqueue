from __future__ import annotations
import subprocess

from myqueue.task import Task
from myqueue.queue import Queue


def run_tasks(tasks: list[Task]) -> None:
    for task in tasks:
        cmd = str(task.cmd)
        print(f'{task.folder}: {cmd}')
        cmd = 'MPLBACKEND=Agg ' + cmd
        cmd = f'cd {task.folder} && {cmd}'
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0


def run(queue: Queue,
        tasks: list[Task]) -> None:
    """Run tasks locally."""
    1 / 0
    # dnames = {task.dname for task in tasks}
    # queue._remove([task for task in queue.tasks if task.dname in dnames])
    if queue.dry_run:
        for task in tasks:
            print(f'{task.folder}: {task.cmd}')
    else:
        run_tasks(tasks)
