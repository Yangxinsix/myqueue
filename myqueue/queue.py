from myqueue.task import Task


class Queue:
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
        return LocalQueue()
    if 'slurm'.startswith(name):
        from myqueue.slurm import SLURM
        return SLURM()
    else:
        assert 0
