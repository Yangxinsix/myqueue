from pathlib import Path
from typing import Set, List, Tuple
from myqueue.task import Task
from myqueue.config import Configuration


class Scheduler:
    def __init__(self, config: Configuration):
        self.config = config
        self.name = config.scheduler.lower()

    def submit(self, task: Task, dry_run: bool, verbose: bool) -> None:
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

    def get_config(self, queue: str = '') -> Tuple[List[Tuple[str, int, str]],
                                                   List[str]]:
        raise NotImplementedError


def get_scheduler(config: Configuration) -> Scheduler:
    name = config.scheduler.lower()
    if name == 'test':
        from myqueue.test.scheduler import TestScheduler as S
    elif name == 'local':
        from myqueue.local import LocalScheduler as S
    elif name == 'slurm':
        from myqueue.slurm import SLURM as S
    elif name == 'pbs':
        from myqueue.pbs import PBS as S
    elif name == 'lsf':
        from myqueue.lsf import LSF as S
    else:
        raise ValueError(f'Unknown scheduler: {name}')
    return S(config)
