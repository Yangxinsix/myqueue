from __future__ import annotations

from pathlib import Path

from myqueue.config import Configuration
from myqueue.task import Task


class SchedulerError(Exception):
    """Error from scheduler command."""


class Scheduler:
    def __init__(self, config: Configuration):
        self.config = config
        self.name = config.scheduler.lower()

    def submit(self,
               task: Task,
               dry_run: bool = False,
               verbose: bool = False) -> None:
        """Submit a task."""
        pass

    def cancel(self, task: Task) -> None:
        """Cancel a task."""
        raise NotImplementedError

    def get_ids(self) -> set[str]:
        """Get ids for all tasks the scheduler knows about."""
        raise NotImplementedError

    def hold(self, task: Task) -> None:
        raise NotImplementedError

    def release_hold(self, task: Task) -> None:
        raise NotImplementedError

    def error_file(self, task: Task) -> Path:
        return task.folder / f'{task.cmd.short_name}.{task.id}.err'

    def has_timed_out(self, task: Task) -> bool:
        path = self.error_file(task).expanduser()
        if path.is_file():
            task.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines:
                if line.endswith('DUE TO TIME LIMIT ***'):
                    return True
        return False

    def maxrss(self, id: str) -> int:
        return 0

    def get_config(self, queue: str = '') -> tuple[list[tuple[str, int, str]],
                                                   list[str]]:
        raise NotImplementedError


def get_scheduler(config: Configuration) -> Scheduler:
    """Create scheduler from config object."""
    name = config.scheduler.lower()
    if name == 'test':
        from myqueue.test.scheduler import TestScheduler
        assert TestScheduler.current_scheduler is not None
        return TestScheduler.current_scheduler
    if name == 'local':
        from myqueue.local import LocalScheduler
        return LocalScheduler(config)
    if name == 'slurm':
        from myqueue.slurm import SLURM
        return SLURM(config)
    if name == 'pbs':
        from myqueue.pbs import PBS
        return PBS(config)
    if name == 'lsf':
        from myqueue.lsf import LSF
        return LSF(config)
    raise ValueError(f'Unknown scheduler: {name}')
