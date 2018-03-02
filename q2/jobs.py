import json
from pathlib import Path
from typing import Set, List

from q2.job import Job
from q2.runner import Runner, get_runner
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

    @lock
    def list(self, states: Set[str]) -> None:
        self._read()
        for job in self.jobs:
            if job.state in states:
                print(job)

    @lock
    def submit(self, jobs: List[Job], runner: Runner) -> None:
        self._read()
        for job in jobs:
            job.state = 'queued'
        runner.submit(jobs)
        self.jobs += jobs
        self._write()
        runner.kick()

    @lock
    def update(self, uid: str, state: str) -> None:
        self._read()
        for job in self.jobs:
            if job.uid == uid:
                break
        else:
            raise ValueError('No such job: {uid}, {state}')

        if state == 'running':
            job.state = 'running'
        elif state == 'done':
            jobs = []
            for j in self.jobs:
                if j is not job:
                    if uid in j.deps:
                        j.deps.remove(uid)
                    jobs.append(j)
            self.jobs = jobs
        else:
            assert state == 'FAILED'
            job.state = 'FAILED'
            for j in self.jobs:
                if j is not job:
                    if uid in j.deps:
                        j.deps.remove(uid)
                    j.state = 'CANCELED'

        self._write()

        if state != 'running':
            job.remove_empty_output_files()

        if job.runner == 'local':
            if state != 'running':
                # Process local queue:
                runner = get_runner('local')
                runner.update(uid, state)
                runner.kick()

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
    uid, state = sys.argv[1:3]
    jobs = Jobs()
    try:
        jobs.update(uid, state)
    except Exception as x:
        raise
