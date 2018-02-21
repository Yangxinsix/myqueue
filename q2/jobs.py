import json
from pathlib import Path

from q2.utils import Lock
from q2.job import Job


def lock(method):
    def m(self, *args, **kwargs):
        print(method)
        with self.lock:
            print(method, 2)
            self._read()
            result = method(self, *args, **kwargs)
            self._write()
            return result
    return m


class JobList:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run

        folder = self.fname = Path.home() / '.cmr'

        if not folder.is_dir():
            folder.mkdir()

        self.fname = folder / 'queue.json'
        self.lock = Lock(self.fname.with_name('queue.json.lock'))

        self.jobs = None

        self.runners = {}

    def get_runner(self, name):
        if name not in self.runners:
            if name == 'local':
                self.runners[name] = LocalRunner()
            elif name == 'slurm':
                ...
        return self.runners[name]

    @lock
    def submit(self, newjobs):
        for job in newjobs:
            job.state = 'queued'
            runner = self.get_runner(job.queue)
            job.jobid = runner.submit(job)
            self.jobs.append(job)

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

    def _read(self):
        if not self.fname.is_file():
            return {}

        data = json.loads(self.fname.read_text())

        self.jobs = {}
        for id, folder, name, deps, state, queue, flow in data['jobs']:
            job = Job(name,
                      deps=deps,
                      folder=Path(folder),
                      flow=flow,
                      state=state,
                      queue=queue)
            job.jobid = id
            self.jobs[job.uid] = job

    def _write(self):
        text = json.dumps({'jobs': [job.astuple()
                                    for job in self.jobs.values]})
        self.fname.write_text(text)




if __name__ == '__main__':
    import sys
    state, uname = sys.argv[1:3]
    JobList().update(state, uname)
