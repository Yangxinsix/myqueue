from myqueue.task import Task
from typing import Set


class Queue:
    def submit(self, task: Task) -> None:
        pass

    def update(self, id: int, state: str) -> None:
        pass

    def kick(self) -> None:
        pass

    def timeout(self, Task) -> bool:
        return False

    def cancel(self, task: Task) -> None:
        raise NotImplementedError

    def get_ids(self) -> Set[int]:
        raise NotImplementedError

    def hold(self, task: Task) -> None:
        raise NotImplementedError

    def release_hold(self, task: Task) -> None:
        raise NotImplementedError


def get_queue(name: str) -> Queue:
    if 'local'.startswith(name):
        from myqueue.local import LocalQueue
        return LocalQueue()
    if 'slurm'.startswith(name):
        from myqueue.slurm import SLURM
        return SLURM()
    if 'pbs'.startswith(name):
        from myqueue.pbs import PBS
        return PBS()
    else:
        assert 0
