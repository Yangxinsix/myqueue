import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Set, List, Dict  # noqa

from q2.job import Job
from q2.runner import get_runner
from q2.utils import Lock
from q2.config import home_folder


def pjoin(folder, reldir):
    assert reldir == '.'
    return folder


def S(n, thing):
    if n == 1:
        return '1 ' + thing
    return '{} {}s'.format(n, thing)


def colored(state: str) -> str:
    if state.isupper():
        return '\033[91m' + state + '\033[0m'
    if state.startswith('done'):
        return '\033[92m' + state + '\033[0m'
    return state


def pprint(jobs: List[Job],
           verbosity: int = 1,
           columns: str = 'ifnraste') -> None:

    if verbosity < 0:
        return

    if not jobs:
        print('No jobs')
        return

    color = sys.stdout.isatty()
    home = str(Path.home())

    titles = ['id', 'folder', 'name', 'res.', 'age', 'state', 'time', 'error']
    c2i = {title[0]: i for i, title in enumerate(titles)}
    indices = [c2i[c] for c in columns]

    if verbosity:
        lines = [[titles[i] for i in indices], None]
        lengths = [len(t) for t in lines[0]]
    else:
        lines = []
        lengths = [0] * len(columns)

    count = defaultdict(int)  # type: Dict[str, int]
    for job in jobs:
        words = job.words()
        _, folder, _, _, _, state, _, error = words
        count[state] += 1
        if folder.startswith(home):
            words[1] = '~' + folder[len(home):]
        words = [words[i] for i in indices]
        lines.append(words)
        lengths = [max(n, len(word)) for n, word in zip(lengths, words)]

    try:
        N = os.get_terminal_size().columns
        cut = max(0, N - sum(L + 1 for L, c in zip(lengths, columns)
                             if c != 'e'))
    except OSError:
        cut = 999999

    if verbosity:
        lines[1] = ['-' * L for L in lengths]
        lines.append(lines[1])

    for words in lines:
        words2 = []
        for word, c, L in zip(words, columns, lengths):
            if c == 'e':
                word = word[:cut]
            elif c in 'at':
                word = word.rjust(L)
            else:
                word = word.ljust(L)
                if c == 's' and color:
                    word = colored(word)
            words2.append(word)
        print(' '.join(words2))

    if verbosity:
        print(', '.join('{}: {}'.format(state, n)
                        for state, n in count.items()))


class Queue(Lock):
    def __init__(self, runner: str, verbosity: int = 1) -> None:
        self.runner = get_runner(runner)
        self.verbosity = verbosity

        self.debug = bool(os.environ.get('Q2_DEBUG'))

        folder = home_folder()

        if not folder.is_dir():
            folder.mkdir()

        self.fname = folder / (runner + '.json')

        Lock.__init__(self, self.fname.with_name(runner + '.json.lock'))

        self.jobs = None  # type: List[Job]

    def list(self,
             id: int,
             name: str,
             states: Set[str],
             folders,
             columns: str) -> List[Job]:
        self._read()
        jobs = self.select(id, name, states, folders, recursive=True)
        pprint(jobs, self.verbosity, columns)
        return jobs

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

        jobs2 = []
        for job in jobs:
            if job.workflow and (job.folder, job.cmd.name) in current:
                job.id = current[(job.folder, job.cmd.name)].id
            else:
                jobs2.append(job)
        jobs = jobs2

        n3 = len(jobs)

        if n3 < n2:
            print(S(n2 - n3, 'job'), 'already in the queue')

        ready = []
        for job in jobs:
            deps = []
            for dep in job.deps:
                if isinstance(dep, str):
                    # convert str to Job:
                    reldir, _, name = dep.rpartition('/')
                    if not reldir:
                        reldir = '.'
                    folder = pjoin(job.folder, reldir)
                    j = current.get((folder, name))
                    if j is None:
                        for jj in jobs:
                            if jj.folder == folder and jj.cmd.name == name:
                                j = jj
                                break
                        else:
                            if not (folder / (name + '.done')).is_file():
                                print('Missing dependency: {}/{}'
                                      .format(folder, name))
                                break
                    elif j.state == 'done':
                        j = None
                    elif j.state not in ['queued', 'running']:
                        print('Dependency ({}) in bad state: {}'
                              .format(j.name, j.state))
                        break

                    dep = j

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
            pprint(ready, 0, 'fnr')
        else:
            self.runner.submit(ready)
            print(S(len(ready), 'job'), 'submitted:')
            pprint(ready, 0, 'ifnr')

        if not dry_run:
            self.jobs += ready
            self._write()
            self.runner.kick()

    def select(self, id: int,
               name: str,
               states: Set[str],
               folders: List[str],
               recursive: bool = False) -> List[Job]:
        if id is not None:
            for job in self.jobs:
                if job.id == id:
                    return [job]
            return []

        jobs = []
        for job in self.jobs:
            if job.state in states:
                if not name or job.cmd.name == name:
                    if any(job.infolder(f, recursive) for f in folders):
                        jobs.append(job)

        return jobs

    def delete(self,
               id: int,
               name: str,
               states: Set[str],
               folders: List[str],
               recursive: bool,
               dry_run: bool) -> None:
        """Delete or cancel jobs."""

        self._read()

        jobs = self.select(id, name, states, folders, recursive)

        t = time.time()
        for job in jobs:
            if job.tstop is None:
                job.tstop = t

        if dry_run:
            print(S(len(jobs), 'job'), 'to be deleted')
            pprint(jobs, 0, 'ifnr')
        else:
            print(S(len(jobs), 'job'), 'deleted')
            pprint(jobs, 0, 'ifnr')
            for job in jobs:
                if job.state in ['running', 'queued']:
                    self.runner.cancel(job)
                self.jobs.remove(job)
            self._write()

    def find_depending(self, jobs):
        map = {(job.folder, job.cmd.name): job for job in self.jobs}
        d = defaultdict(list)
        for job in self.jobs:
            for dep in job.deps:
                j = map[(job.folder, dep)]
                d[j].append(job)

        removed = []

        def remove(job):
            removed.apend(job)
            for j in d[job]:
                remove(j)

        for job in jobs:
            remove(job)

        return removed

    def resubmit(self,
                 id: int,
                 name: str,
                 states: Set[str],
                 folders: List[str],
                 recursive: bool,
                 dry_run: bool,
                 cores: int,
                 tmax: int) -> None:

        self._read()
        jobs = []
        for job in self.select(id, name, states, folders, recursive):
            if job.state.isupper():
                self.jobs.remove(job)
            job = Job(job.cmd, deps=job.deps, tmax=job.tmax, cores=job.cores,
                      folder=job.folder, repeat=job.repeat,
                      workflow=job.workflow)
            if cores:
                job.cores = cores
            if tmax:
                job.tmax = tmax
            jobs.append(job)
        self.submit(jobs, dry_run)

    def update(self, id: int, state: str) -> None:
        if self.debug:
            print('UPDATE', id, state)

        if not state.isalpha():
            if state == '0':
                state = 'done'
            else:
                state = 'FAILED'

        self._read()
        for job in self.jobs:
            if job.id == id:
                break
        else:
            raise ValueError('No such job: {id}, {state}'
                             .format(id=id, state=state))

        t = time.time()

        job.state = state

        if state == 'done':
            for j in self.jobs:
                if id in j.deps:
                    j.deps.remove(id)
            if job.workflow:
                job.write_done_file()
            job.tstop = t

        elif state == 'running':
            job.trunning = t

        elif state == 'FAILED':
            for j in self.jobs:
                if id in j.deps:
                    j.state = 'CANCELED'
                    j.tstop = t
            job.tstop = t

        elif state == 'TIMEOUT':
            job.state = 'running'

        else:
            1 / 0

        self._write()

        if state != 'running':
            # Process local queue:
            self.runner.update(id, state)
            self.runner.kick()
            job.remove_empty_output_files()

    def _read(self) -> None:
        self.jobs = []

        if not self.fname.is_file():
            return

        data = json.loads(self.fname.read_text())

        for dct in data['jobs']:
            job = Job.fromdict(dct)
            self.jobs.append(job)

        self.check()

    def _write(self):
        text = json.dumps({'jobs': [job.todict()
                                    for job in self.jobs]},
                          indent=1)
        self.fname.write_text(text)

    def check(self) -> None:
        write = False
        dct = {job.id: job for job in self.jobs}
        t = time.time()
        for job in self.jobs:
            if job.state == 'running':
                if t - job.trunning > job.tmax and self.runner.timeout(job):
                    job.state = 'TIMEOUT'
                    job.remove_empty_output_files()
                    for j in self.jobs:
                        if job.id in j.deps:
                            j.state = 'CANCELED'
                            j.tstop = t
                    write = True
            elif job.state == 'queued':
                for id in job.deps:
                    if dct[id].state.isupper():
                        job.state = 'CANCELED'
                        job.tstop = t
            elif job.state == 'FAILED':
                if job.error is None:
                    job.read_error()
                    write = True
        if write:
            self._write()


if __name__ == '__main__':
    runner, id, state = sys.argv[1:4]
    q = Queue(runner, 0)
    try:
        with q:
            q.update(int(id), state)
    except Exception as x:
        raise
