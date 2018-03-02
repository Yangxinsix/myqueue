import json
import subprocess
from pathlib import Path

from q2.job import Job
from q2.utils import lock, Lock, f


class LocalRunner:
    def __init__(self):
        self.fname = Path.home() / '.q2' / 'runner.json'
        self.lock = Lock(self.fname.with_name('runner.json.lock'))
        self.jobs = None

    @lock
    def submit(self, jobs):
        self._read()
        self.jobs += jobs
        self._write()

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
    def kick(self):
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

    def write(self):
        text = json.dumps({'running': self.running})
        self.path.write_text(text)

        self.lock = Lock(self.fname.with_name('queue.json.lock'))

        self.running = 0
        self.nextid = 1

    def _step(self, jobs: dict) -> None:
        if self.running >= self.size:
            return

        for id in sorted(jobs):
            job = jobs[id]
            if (not job.deps and
                job.state == 'queued' and
                job.queue == 'local'):
                break
        else:
            return

        cmd = job.command()
        done = 'python3 -m c2dm.jobs.queue done {}'.format(id)
        fail = 'python3 -m c2dm.jobs.queue FAILED {}'.format(id)
        cmd = '(({cmd} && {done}) || {fail})&'.format(cmd=cmd, done=done,
                                                      fail=fail)
        print(cmd)
        subprocess.run(cmd, shell=True)

        job.state = 'running'
        self.running += 1
        self._write(jobs)

        self._step(jobs)

    @lock
    def updateeee(self, state: str, id: int) -> None:
        jobs = self._read()
        if state == 'done':
            job = jobs.pop(id)
            for t in jobs.values():
                if id in t.deps:
                    t.deps.remove(id)
        else:
            assert state == 'FAILED'
            job = jobs[id]
            job.state = 'FAILED'
            jobs = {id: t for id, t in jobs.items() if id not in t.deps}

        if job.queue == 'local':
            self.running -= 1

        self._write(jobs)

        self._step(jobs)

    @lock
    def read(self):
        return self._read()
