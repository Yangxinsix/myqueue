import json
from pathlib import Path
from typing import Set, List

from q2.job import Job
from q2.runner import Runner
from q2.utils import Lock, lock


class Jobs:
    def __init__(self, verbosity=1):
        self.verbosity = verbosity

        folder = Path.home() / '.q2'

        if not folder.is_dir():
            folder.mkdir()

        self.fname = folder / 'queue.json'
        self.lock = Lock(self.fname.with_name('queue.json.lock'))

        self.jobs = None

    @lock(readonly=True)
    def list(self, states: Set[str]) -> None:
        for job in self.jobs:
            if job.state in states:
                print(job)

    @lock
    def submit(self, jobs: List[Job], runner: Runner) -> None:
        for job in jobs:
            job.state = 'queued'
        runner.submit(jobs)
        self.jobs += jobs

    @lock
    def update(self, state: str, uid: str) -> None:
        if state == 'done':
            job = self.jobs.pop(uid)
            for j in self.jobs.values():
                if uid in j.deps:
                    j.deps.remove(uid)
        else:
            assert state == 'FAILED'
            job = self.jobs[uid]
            job.state = 'FAILED'
            self.jobs = {uid: j
                         for uid, j in self.jobs.items()
                         if uid not in j.deps}

        if job.runner == 'local':
            # Process local queue:
            runner = self.get_runner('local')
            runner.running -= 1
            runner.write()
            for job in self.jobs:
                if runner.full():
                    break
                ready = (not job.deps and
                         job.state == 'queued' and
                         job.queue == 'local')
                if ready:
                    runner.run(job)

    def _read(self) -> None:
        self.jobs = []

        if not self.fname.is_file():
            return

        data = json.loads(self.fname.read_text())

        for tpl in data['jobs']:
            job = Job.fromtuple(tpl)
            self.jobs.append(job)

    def _write(self):
        text = json.dumps({'jobs': [job.astuple()
                                    for job in self.jobs]})
        self.fname.write_text(text)


if __name__ == '__main__':
    import sys
    state, uname = sys.argv[1:3]
    Jobs().update(state, uname)
