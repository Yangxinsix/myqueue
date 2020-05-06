from pathlib import Path
from typing import Set, List, Tuple
from myqueue.task import Task


class Scheduler:
    name: str

    def submit(self, task: Task, dry_run: bool) -> None:
        pass

    def cancel(self, task: Task) -> None:
        raise NotImplementedError

    def get_ids(self) -> Set[int]:
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

    def maxrss(self, id: int) -> int:
        return 0

    def get_config(self) -> List[Tuple[str, int, str]]:
        raise NotImplementedError


def get_scheduler(name: str) -> Scheduler:
    name = name.lower()
    if name == 'test':
        from myqueue.test.scheduler import TestScheduler
        assert TestScheduler.current_scheduler is not None
        scheduler: Scheduler = TestScheduler.current_scheduler
    elif name == 'local':
        from myqueue.local import LocalScheduler
        scheduler = LocalScheduler()
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
