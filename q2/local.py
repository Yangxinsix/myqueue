import json
import subprocess
from pathlib import Path

from ase.utils import Lock

from q2.job import Job


def lock(method):
    def m(self, *args, **kwargs):
        print(method)
        with self.lock:
            print(method, 2)
            return method(self, *args, **kwargs)
    return m

class LocalRunner:
    def __init__(self):
        self.path = Path.home() / '.cmr/local.json'
        if not self.path.is_file():
            self.running = 0
        else:
            self.running = json.loads(self.path.read_text())['running']

        self.size = 1

    def full(self):
        return self.running >= self.size

    def submit(self, job):
        if not self.full():
            self.run(job)

    def run(self, job):
        cmd = job.command()
        done = 'python3 -m c2dm.jobs.joblist done {}'.format(job.uid)
        fail = 'python3 -m c2dm.jobs.joblist FAILED {}'.format(job.uid)
        cmd = '(({cmd} && {done}) || {fail})&'.format(cmd=cmd, done=done,
                                                      fail=fail)
        print(cmd)
        p = subprocess.run(cmd, shell=True)
        print(p.pid)
        job.state = 'running'
        self.running += 1
        self.write()

    def write(self):
        text = json.dumps({'running': self.running})
        self.path.write_text(text)

class JobList:
    def __init__(self, size=1, dry_run=False, max_submit=100):
        self.size = size
        self.dry_run = dry_run
        self.max_submit = max_submit

        folder = self.fname = Path.home() / '.cmr'

        if not folder.is_dir():
            folder.mkdir()

        self.fname = folder / 'queue.json'
        self.lock = Lock(self.fname.with_name('queue.json.lock'))

        self.running = 0
        self.nextid = 1

    @lock
    def submit(self, job):
        jobs = self._read()
        job.state = 'queued'
        id = self.nextid
        self.nextid += 1
        job.jobid = id
        jobs[id] = job
        self._write(jobs)
        self._step(jobs)
        return id

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
    def update(self, state: str, id: int) -> None:
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

    def _read(self):
        if not self.fname.is_file():
            return {}

        data = json.loads(self.fname.read_text())

        self.nextid = data['nextid']
        self.running = data['running']

        jobs = {}
        for id, folder, name, deps, state, queue, flow in data['jobs']:
            jobs[id] = Job(name,
                            deps=deps,
                            folder=Path(folder),
                            flow=flow,
                            state=state,
                            queue=queue)
            jobs[id].jobid = id

        return jobs

    def _write(self, jobs):
        text = json.dumps({'nextid': self.nextid,
                           'running': self.running,
                           'jobs': [job.astuple() for task in jobs.values()]})
        self.fname.write_text(text)


if __name__ == '__main__':
    import sys
    state = sys.argv[1]
    id = int(sys.argv[2])
    Queue().update(state, id)
