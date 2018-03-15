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
                       zip(lengths, str(job).split())))


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

    def list(self, states: Set[str]) -> None:
        self._read()

        write = False
        repeats = []
        t = time.time()
        for job in self.jobs:
            if job.state == 'running':
                if t - job.tstart > job.time and self.runner.timeout(job):
                    job.state = 'TIMEOUT'
                    write = True
                    if job.repeat > 0:
                        repeats.append(job)

        pprint([job for job in self.jobs if job.state in states])

        if repeats:
            for job in repeats:
                self.jobs.remove(job)
                job.repeats -= 1
            self.submit(repeats)
        elif write:
            self._write()

    def submit(self,
               jobs: List[Job],
               workflow: bool = False,
               dry_run: bool = False) -> None:

        n1 = len(jobs)
        if workflow:
            jobs = [job for job in jobs if not job.done()]
        n2 = len(jobs)

        if n2 < n1:
            print(S(n1 - n2, 'job'), 'already done')

        if self.jobs is None:
            self._read()

        current = {(job.folder, job.cmd.name): job
                   for job in self.jobs}

        jobs = [job for job in jobs
                if (job.folder, job.cmd.name) not in current]
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

        for job in ready:
            job.deps = [dep for dep in job.deps if not dep.done()]
            job.state = 'queued'

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

    def cancel(self,
               states: Set[str],
               id: int,
               folders: List[str],
               dry_run: bool) -> None:
        """Cancel jobs."""

        self._read()

        jobs = []
        for job in self.jobs:
            if job.state in states:
                if id is None or job.id == id:
                    if not folders or any(job.infolder(f) for f in folders):
                        jobs.append(job)

        for job in jobs:
            job.state = 'CANCELED'

        if dry_run:
            print(S(len(jobs), 'job'), 'to be canceled')
            pprint(jobs)
        else:
            print(S(len(jobs), 'job'), 'canceled')
            pprint(jobs)
            for job in jobs:
                self.runner.cancel(job)
                self.jobs.remove(job)
            self._write()

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

        if resubmit:
            self.submit(jobs, dry_run)
        else:
            for job in jobs:
                job.state = 'REMOVED'
            if dry_run:
                print(S(len(jobs), 'job'), 'to reset')
                pprint(jobs)
            else:
                print(S(len(jobs), 'job'), 'reset')
                pprint(jobs)
                for job in jobs:
                    self.jobs.remove(job)
                self._write()

    def update(self, id: str, state: str) -> None:
        self._read()
        for job in self.jobs:
            if job.id == id:
                break
        else:
            raise ValueError('No such job: {id}, {state}'
                             .format(id=id, state=state))

        job.state = state

        if state == 'done':
            for j in self.jobs:
                if id in j.deps:
                    j.deps.remove(id)
            job.write_done_file()

        elif state == 'FAILED':
            for j in self.jobs:
                if id in j.deps:
                    j.state = 'CANCELED'
            job.read_error()
            if job.out_of_memory and len(job.cores) > 1:
                del job.cores[0]
                job.state = 'run with more cores'

        elif state == 'running':
            job.tstart = time.time()

        else:
            1 / 0

        self._write()

        if state != 'running':
            job.remove_empty_output_files()

        if state != 'running':
            # Process local queue:
            self.runner.update(id, state)
            self.runner.kick()

        if job.state == 'run with more cores':
            self.submit([job])

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
    runner, id, state = sys.argv[1:4]
    q = Queue(runner, 0)
    try:
        with q:
            q.update(int(id), state)
    except Exception as x:
        raise
