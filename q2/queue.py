import json
import time
from pathlib import Path
from typing import Set, List

from q2.job import Job
from q2.runner import get_runner
from q2.utils import Lock


def pjoin(folder, reldir):
    assert reldir == '.'
    return folder


def S(n, thing):
    if n == 1:
        return '1 ' + thing
    return '{} {}s'.format(n, thing)


def pprint(jobs):
    lengths = [0, 0, 0, 0, 0]
    for job in jobs:
        lengths = [max(n, len(word))
                   for n, word in zip(lengths, str(job).split())]
    lengths.append(1)
    for job in jobs:
        print(' '.join(word.ljust(n)
                       for n, word in
                       zip(lengths, str(job).split(None, 5))))


class Queue(Lock):
    def __init__(self, runner, verbosity=1):
        self.runner = get_runner(runner)
        self.verbosity = verbosity

        folder = Path.home() / '.q2'

        if not folder.is_dir():
            folder.mkdir()

        self.fname = folder / (runner + '.json')

        Lock.__init__(self, self.fname.with_name(runner + '.json.lock'))

        self.jobs = None

    def list(self, states: Set[str], folders) -> None:
        self._read()

        write = False
        again = []
        t = time.time()
        for job in self.jobs:
            if job.state == 'running':
                if t - job.trunning > job.tmax and self.runner.timeout(job):
                    job.state = 'TIMEOUT'
                    job.remove_empty_output_files()
                    write = True
                    if job.repeat > 0:
                        job.repeat -= 1
                        again.append(job)
            elif job.state == 'FAILED':
                if job.error is None:
                    job.read_error()
                    write = True
                if len(job.cores) > 1 and job.out_of_memory:
                    del job.cores[0]
                    again.append(job)

        for job in again:
            self.jobs.remove(job)

        pprint([job for job in self.jobs
                if job.state in states and
                (not folders or any(job.infolder(f) for f in folders))])

        if again:
            self.submit(again)
        elif write:
            self._write()

    def submit(self,
               jobs: List[Job],
               dry_run: bool = False) -> None:

        n1 = len(jobs)
        jobs = [job for job in jobs if not job.workflow or not job.done()]
        n2 = len(jobs)

        if n2 < n1:
            print(S(n1 - n2, 'job'), 'already done')

        if self.jobs is None:
            self._read()

        current = {(job.folder, job.cmd.name): job
                   for job in self.jobs}

        jobs = [job for job in jobs
                if not job.workflow or
                (job.folder, job.cmd.name) not in current]
        n3 = len(jobs)

        if n3 < n2:
            print(S(n2 - n3, 'job'), 'already in the queue')

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

        t = time.time()
        for job in ready:
            job.deps = [dep for dep in job.deps if not dep.done()]
            job.state = 'queued'
            job.tqueued = t

        if dry_run:
            print(S(len(ready), 'job'), 'to submit:')
        else:
            self.runner.submit(ready)
            print(S(len(ready), 'job'), 'submitted:')

        pprint(ready)

        if not dry_run:
            self.jobs += ready
            self._write()
            self.runner.kick()

    def delete(self,
               states: Set[str],
               id: int,
               folders: List[str],
               dry_run: bool) -> None:
        """Delete or cancel jobs."""

        self._read()

        jobs = []
        for job in self.jobs:
            if job.state in states:
                if id is None or job.id == id:
                    if not folders or any(job.infolder(f) for f in folders):
                        jobs.append(job)

        for job in jobs:
            job.state = 'DELETED'

        if dry_run:
            print(S(len(jobs), 'job'), 'to be deleted')
            pprint(jobs)
        else:
            print(S(len(jobs), 'job'), 'deleted')
            pprint(jobs)
            for job in jobs:
                if job.state in ['running', 'queued']:
                    self.runner.cancel(job)
                self.jobs.remove(job)
            self._write()

    def update(self, id: int, state: str) -> None:
        self._read()
        for job in self.jobs:
            if job.id == id:
                break
        else:
            raise ValueError('No such job: {id}, {state}'
                             .format(id=id, state=state))

        job.state = state

        t = time.time()

        if state == 'done':
            for j in self.jobs:
                if id in j.deps:
                    j.deps.remove(id)
            if job.workflow:
                job.write_done_file()
            job.tstop = t

        elif state == 'FAILED':
            for j in self.jobs:
                if id in j.deps:
                    j.state = 'CANCELED'
            job.tstop = t

        elif state == 'running':
            job.trunning = t

        else:
            1 / 0

        self._write()

        if state != 'running':
            job.remove_empty_output_files()

        if state != 'running':
            # Process local queue:
            self.runner.update(id, state)
            self.runner.kick()

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
                                    for job in self.jobs]},
                          indent=1)
        self.fname.write_text(text)


if __name__ == '__main__':
    import sys
    runner, id, state = sys.argv[1:4]
    q = Queue(runner, 0)
    try:
        with q:
            q.update(int(id), state)
    except Exception as x:
        raise
