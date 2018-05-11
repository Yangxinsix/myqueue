from myqueue.task import Task


class Queue:
    def __init__(self, name):
        self.name = name

    def submit(self, task: Task) -> None:
        pass

    def update(self, id: int, state: str) -> None:
        pass

    def kick(self) -> None:
        pass

    def timeout(self, Task):
        return False

    def cancel(self, tas: Task):
        raise NotImplementedError


def get_queue(name: str) -> Queue:
    if 'local'.startswith(name):
        from myqueue.local import LocalQueue
        return LocalQueue(name)
    if 'slurm'.startswith(name):
        from myqueue.slurm import SLURM
        return SLURM(name)
    else:
        assert 0
