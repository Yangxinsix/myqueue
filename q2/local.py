import json
import subprocess
from pathlib import Path
from typing import List

from q2.job import Job
from q2.utils import lock, Lock, f
from q2.runner import Runner


class LocalRunner(Runner):
    def __init__(self):
        self.fname = Path.home() / '.q2' / 'runner.json'
        self.lock = Lock(self.fname.with_name('runner.json.lock'))
        self.jobs = None
        self.number = None

    @lock
    def submit(self, jobs: List[Job]) -> None:
        self._read()
        for job in jobs:
            self.number += 1
            job.id = self.number
            self.jobs.append(job)
        self._write()

    def _read(self) -> None:
        self.jobs = []

        if not self.fname.is_file():
            self.number = 0
            return

        data = json.loads(self.fname.read_text())

        for dct in data['jobs']:
            job = Job.fromdict(dct)
            self.jobs.append(job)

        self.number = data['number']

    def _write(self):
        text = json.dumps({'jobs': [job.todict()
                                    for job in self.jobs],
                           'number': self.number})
        self.fname.write_text(text)

    @lock
    def update(self, uid: str, state: str) -> None:
        self._read()
        for job in self.jobs:
            if job.uid == uid:
                break
        else:
            raise ValueError(f**'No such job: {uid}, {state}')

        if state == 'done':
            jobs = []
            for j in self.jobs:
                if j is not job:
                    if uid in j.deps:
                        j.deps.remove(uid)
                    jobs.append(j)
            self.jobs = jobs
        else:
            assert state == 'FAILED', state
            jobs = []
            for j in self.jobs:
                if j is not job and uid not in j.deps:
                    jobs.append(j)
            self.jobs = jobs

        self._write()

    @lock
    def kick(self) -> None:
        self._read()
        for job in self.jobs:
            if job.state == 'running':
                return

        for job in self.jobs:
            if job.state == 'queued' and not job.deps:
                break
        else:
            return

        self._run(job)
        self._write()

    def _run(self, job):
        cmd = job.command()
        msg = 'python3 -m q2.jobs {}'.format(job.uid)
        cmd = ('(({msg} running && {cmd} && {msg} done) || {msg} FAILED)&'
               .format(cmd=cmd, msg=msg))
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0
        job.state = 'running'
