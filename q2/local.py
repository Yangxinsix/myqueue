import json
import subprocess
from typing import List


from q2.config import home_folder
from q2.job import Job
from q2.runner import Runner


class LocalRunner(Runner):
    def __init__(self):
        self.fname = home_folder() / 'local-runner.json'
        self.jobs = None
        self.number = None

    def submit(self, jobs: List[Job], extra: str = None) -> None:
        self._read()
        for job in jobs:
            self.number += 1
            job.id = self.number
            job.deps = [dep.id for dep in job.deps]
            self.jobs.append(job)
        self._write()

    def cancel(self, job):
        assert job.state == 'queued', job
        self._read()
        for i, j in enumerate(self.jobs):
            if job.id == j.id:
                break
        else:
            raise ValueError('No such job!')
        del self.jobs[i]
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

    def update(self, id: int, state: str) -> None:
        self._read()
        for job in self.jobs:
            if job.id == id:
                break
        else:
            raise ValueError('No such job: {id}, {state}'
                             .format(id=id, state=state))

        if state == 'done':
            jobs = []
            for j in self.jobs:
                if j is not job:
                    if id in j.deps:
                        j.deps.remove(id)
                    jobs.append(j)
            self.jobs = jobs
        else:
            assert state in ['FAILED', 'TIMEOUT'], state
            jobs = []
            for j in self.jobs:
                if j is not job and id not in j.deps:
                    jobs.append(j)
            self.jobs = jobs

            if state == 'TIMEOUT':
                path = job.folder / (job.name + '.err')
                with open(str(path), 'a') as fd:
                    fd.write('\nTIMEOUT\n')

        self._write()

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

    def timeout(self, job):
        path = job.folder / (job.name + '.err')
        if path.is_file():
            job.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines[::-1]:
                if line.endswith('TIMEOUT'):
                    return True
        return False

    def _run(self, job):
        cmd1 = job.command()
        msg = 'python3 -m q2.queue local {}'.format(job.id)
        err = job.folder / (job.name + '.err')
        cmd = ('(({msg} running ; {cmd} ; {msg} $?)& p1=$!; '
               '(sleep {tmax}; kill $p1 > /dev/null 2>&1; {msg} TIMEOUT)& '
               'p2=$!; wait $p1; '
               'if [ $? -eq 0 ]; then kill $p2 > /dev/null 2>&1; fi)&'
               .format(cmd=cmd1, msg=msg, tmax=job.tmax, err=err))
        print(cmd)
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0
        job.state = 'running'
