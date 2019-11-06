from pathlib import Path
from typing import Set, Optional
from myqueue.task import Task


class Scheduler:
    name: str

    def submit(self, task: Task,
               activation_script: Optional[Path],
               dry_run: bool) -> None:
        pass

    def update(self, id: int, state: str) -> None:
        pass

    def kick(self) -> None:
        pass

    def has_timed_out(self, task: Task) -> bool:
        return False

    def cancel(self, task: Task) -> None:
        raise NotImplementedError

    def get_ids(self) -> Set[int]:
        raise NotImplementedError

    def hold(self, task: Task) -> None:
        raise NotImplementedError

    def release_hold(self, task: Task) -> None:
        raise NotImplementedError


def get_scheduler(name: str) -> Scheduler:
    name = name.lower()
    if name == 'local':
        from myqueue.local import LocalScheduler
        scheduler: Scheduler = LocalScheduler()
    elif name == 'slurm':
        from myqueue.slurm import SLURM
        scheduler = SLURM()
    elif name == 'pbs':
        from myqueue.pbs import PBS
        scheduler = PBS()
    elif name == 'lsf':
        from myqueue.lsf import LSF
        scheduler = LSF()
    else:
        assert 0, name
    scheduler.name = name
    return scheduler
