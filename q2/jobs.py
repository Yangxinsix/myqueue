import json
from collections import defaultdict
from pathlib import Path
from typing import Set, List

from q2.job import Job
from q2.runner import Runner, get_runner
from q2.utils import Lock


def pjoin(folder, reldir):
    assert reldir == '.'
    return folder


def S(n, thing):
    if n == 1:
        return '1 ' + thing
    return '{} {}s'.format(n, thing)


def pprint(jobs):
    lengths = [0, 0, 0, 0]
    for job in jobs:
        lengths = [max(n, len(word))
                   for n, word in zip(lengths, str(job).split())]
    for job in jobs:
        print(' '.join(word.ljust(n)
                       for n, word in
                       zip(lengths, str(job).split())))


class Jobs(Lock):
    def __init__(self, verbosity=1):
        self.verbosity = verbosity

        folder = Path.home() / '.q2'

        if not folder.is_dir():
            folder.mkdir()

        self.fname = folder / 'queue.json'

        Lock.__init__(self, self.fname.with_name('queue.json.lock'))

        self.jobs = None

    def list(self, states: Set[str]) -> None:
        self._read()
        pprint([job for job in self.jobs if job.state in states])

    def submit(self,
               jobs: List[Job],
               runner: Runner,
               dry_run: bool = False) -> None:

        n1 = len(jobs)
        jobs = [job for job in jobs if not job.done()]
        n2 = len(jobs)

        if n2 < n1:
            print(S(n2 - n1, 'job'), 'already done')

        if self.jobs is None:
            self._read()

        current = {(job.folder, job.cmd.name): job
                   for job in self.jobs}

        jobs = [job for job in jobs
                if (job.folder, job.cmd.name) not in current]
        n3 = len(jobs)

        if n3 < n2:
            print(S(n3 - n2, 'job'), 'already in the queue')

        ready = []
        for job in jobs:
            deps = []
            for dep in job.deps:
                if isinstance(dep, tuple):
                    name, reldir = dep
                    folder = pjoin(job.folder, reldir)
                    dep = current.get((folder, name))
                    if dep is None:
                        if not (folder / (name + '.done')).is_file():
                            print('Missing dependency: {}/{}'
                                  .format(folder, name))
                            break
                    elif dep.state not in ['queued', 'running']:
                        print('Dependency ({}) in bad state: {}'
                              .format(dep.name, dep.state))
                        break

                if dep is not None:
                    deps.append(dep)
            else:
                job.deps = deps
                ready.append(job)

        for job in ready:
            job.deps = [dep for dep in job.deps if not dep.done()]
            job.state = 'queued'

        if dry_run:
            print(S(len(ready), 'job'), 'to submit:')
        else:
            runner.submit(ready)
            print(S(len(ready), 'job'), 'submitted:')

        pprint(ready)

        if not dry_run:
            self.jobs += ready
            self._write()
            runner.kick()

    def reset(self,
              states: Set[str],
              id: int,
              folders: List[str],
              resubmit: bool,
              dry_run: bool) -> None:
        self._read()
        jobs = []
        for job in self.jobs:
            if job.state in states:
                if id is None or job.id == id:
                    if not folders or any(job.infolder(f) for f in folders):
                        jobs.append(job)
        if id is not None:
            assert len(jobs) == 1, jobs

        if resubmit:
            runners = defaultdict(list)
            for job in jobs:
                runners[job.runner].append(job)
            for runner, jobs in runners.items():
                runner = get_runner(runner)
                self.submit(jobs, runner, dry_run)
        else:
            for job in jobs:
                job.state = 'REMOVED'
            if dry_run:
                print(S(len(jobs), 'job'), 'to reset')
                pprint(jobs)
            else:
                print(S(len(jobs), 'job'), 'to reset')
                pprint(jobs)
                for job in jobs:
                    self.jobs.remove(job)
                self._write()

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
                        j.state = 'CANCELED'
                j.read_error()

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

        for dct in data['jobs']:
            job = Job.fromdict(dct)
            self.jobs.append(job)

    def _write(self):
        text = json.dumps({'jobs': [job.todict()
                                    for job in self.jobs]})
        self.fname.write_text(text)


if __name__ == '__main__':
    import sys
    uid, state = sys.argv[1:3]
    jobs = Jobs()
    try:
        with jobs:
            jobs.update(uid, state)
    except Exception as x:
        raise
