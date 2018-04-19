from typing import List
from myqueue.job import Job


class Runner:
    def submit(self, jobs: List[Job]) -> None:
        pass

    def update(self, id: int, state: str) -> None:
        pass

    def kick(self) -> None:
        pass

    def timeout(self, job):
        return False

    def cancel(self, job: Job):
        raise NotImplementedError


def get_runner(name: str) -> Runner:
    if 'local'.startswith(name):
        from myqueue.local import LocalRunner
        return LocalRunner()
    if 'slurm'.startswith(name):
        from myqueue.slurm import SLURM
        return SLURM()
    else:
        assert 0
