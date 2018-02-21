import json
import subprocess
from pathlib import Path

from q2.job import Job
from q2.utils import lock, Lock


class LocalRunner:
    def __init__(self):
        self.fname = Path.home() / '.q2' / 'runner.json'
        self.lock = Lock(self.fname.with_name('runner.json.lock'))
        self.jobs = None

    @lock
    def submit(self, jobs):
        self.jobs += jobs

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
    def kick(self):
        for job in self.jobs:
            if job.state == 'running':
                return

    def run(self, job):
        cmd = job.command()
        done = 'python3 -m q2.jobs done {}'.format(job.uid)
        fail = 'python3 -m q2.jobs FAILED {}'.format(job.uid)
        cmd = '(({cmd} && {done}) || {fail})&'.format(cmd=cmd, done=done,
                                                      fail=fail)
        print(cmd)
        p = subprocess.run(cmd, shell=True)
        job.state = 'running'
        self.running += 1
        self.write()

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
