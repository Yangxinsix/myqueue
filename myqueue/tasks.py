import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Set, List, Dict  # noqa

from myqueue.resources import Resources
from myqueue.task import Task
from myqueue.queue import get_queue, Queue
from myqueue.utils import Lock
from myqueue.config import home_folder


class Selection:
    def __init__(self,
                 ids: Set[int],
                 name: str,
                 states: Set[str],
                 folders: List[Path],
                 recursive: bool) -> None:
        self.ids = ids
        self.name = name
        self.states = states
        self.folders = folders
        self.recursive = recursive


class Tasks(Lock):
    def __init__(self, verbosity: int = 1) -> None:
        self.verbosity = verbosity

        self.debug = os.environ.get('MYQUEUE_DEBUG', '')

        self.folder = home_folder()

        if not self.folder.is_dir():
            self.folder.mkdir()

        self.fname = self.folder / 'queue.json'

        Lock.__init__(self, self.fname.with_name('queue.json.lock'))

        self.queues = {}  # type: Dict[str, Queue]
        self.tasks = []  # type: List[Task]
        self.changed = False  # type: bool

    def queue(self, task: Task) -> Queue:
        queuename = task.queue_name()
        queue = self.queues.get(queuename)
        if not queue:
            queue = get_queue(queuename)
            self.queues[queuename] = queue
        return queue

    def __exit__(self, type, value, tb):
        if self.changed:
            self._write()
        Lock.__exit__(self, type, value, tb)

    def list(self, selection: Selection, columns: str) -> List[Task]:
        self._read()
        tasks = self.select(selection)
        pprint(tasks, self.verbosity, columns)
        return tasks

    def submit(self,
               tasks: List[Task],
               dry_run: bool = False,
               read: bool = True) -> None:

        n1 = len(tasks)
        tasks = [task
                 for task in tasks
                 if not task.workflow or not task.done()]
        n2 = len(tasks)

        if n2 < n1:
            print(plural(n1 - n2, 'task'), 'already done')

        if read:
            self._read()

        current = {task.dname: task for task in self.tasks}

        tasks2 = []
        for task in tasks:
            if task.workflow and task.dname in current:
                task.id = current[task.dname].id
            else:
                tasks2.append(task)
        tasks = tasks2

        n3 = len(tasks)

        if n3 < n2:
            print(plural(n2 - n3, 'task'), 'already in the queue')

        todo = []
        for task in tasks:
            task.dtasks = []
            for dep in task.deps:
                # convert dep to Task:
                tsk = current.get(dep)
                if tsk is None:
                    for tsk in tasks:
                        if dep == tsk.dname:
                            break
                    else:
                        donefile = dep.with_name(dep.name + '.done')
                        if not donefile.is_file():
                            print('Missing dependency:', dep)
                            break
                        tsk = None
                elif tsk.state == 'done':
                    tsk = None
                elif tsk.state not in ['queued', 'running']:
                    print('Dependency ({}) in bad state: {}'
                          .format(tsk.name, tsk.state))
                    break

                if tsk is not None:
                    task.dtasks.append(tsk)
            else:
                todo.append(task)

        # All dependensies must have an id or be in the list of tasks
        # about to be submitted
        ready = [task for task in todo
                 if all(tsk.id or tsk in todo
                        for tsk in task.dtasks)]

        t = time.time()
        for task in ready:
            task.dtasks = [tsk for tsk in task.dtasks if not tsk.done()]
            task.state = 'queued'
            task.tqueued = t

        if dry_run:
            pprint(ready, 0, 'fnr')
            print(plural(len(ready), 'task'), 'to submit')
        else:
            submitted = []
            ex = None
            for task in ready:
                try:
                    self.queue(task).submit(task)
                except Exception as x:
                    ex = x
                    break
                else:
                    submitted.append(task)

            pprint(submitted, 0, 'ifnr')
            if submitted:
                print(plural(len(submitted), 'task'), 'submitted')

            self.tasks += submitted
            self.changed = True
            for queue in self.queues.values():
                queue.kick()

            if ex:
                print('ERROR:', task)
                raise ex

    def select(self, s: Selection) -> List[Task]:
        if s.ids is not None:
            return [task for task in self.tasks if task.id in s.ids]

        tasks = []
        for task in self.tasks:
            if task.state in s.states:
                if not s.name or task.cmd.name == s.name:
                    if any(task.infolder(f, s.recursive) for f in s.folders):
                        tasks.append(task)

        return tasks

    def remove(self, selection: Selection, dry_run: bool) -> None:
        """Remove or cancel tasks."""

        self._read()

        tasks = self.select(selection)

        t = time.time()
        for task in tasks:
            if task.tstop is None:
                task.tstop = t

        if dry_run:
            pprint(tasks, 0)
            print(plural(len(tasks), 'task'), 'to be removed')
        else:
            pprint(tasks, 0)
            print(plural(len(tasks), 'task'), 'removed')
            for task in tasks:
                if task.state in ['running', 'queued']:
                    self.queue(task).cancel(task)
                self.tasks.remove(task)
            self.changed = True

    def sync(self, dry_run: bool) -> None:
        self._read()
        alltasks = defaultdict(list)  # type: Dict[Queue, List[Task]]
        for task in self.tasks:
            queue = self.queue(task)
            alltasks[queue].append(task)
        n = 0
        for queue, tasks in alltasks.items():
            ids = queue.get_ids()
            for task in tasks:
                if task.state in ['running', 'queued'] and task.id not in ids:
                    if not dry_run:
                        self.tasks.remove(task)
                        self.changed = True
                    n += 1
        if n:
            if dry_run:
                print(plural(n, 'job'), 'to be removed')
            else:
                print(plural(n, 'job'), 'removed')

    def find_depending(self, tasks: List[Task]):
        map = {task.dname: task for task in self.tasks}
        d = defaultdict(list)  # type: Dict[Task, List[Task]]
        for task in self.tasks:
            for dname in task.deps:
                tsk = map.get(dname)
                if tsk:
                    d[tsk].append(task)

        removed = []

        def remove(task):
            removed.append(task)
            for j in d[task]:
                remove(j)

        for task in tasks:
            remove(task)

        return removed

    def resubmit(self,
                 selection: Selection,
                 dry_run: bool,
                 resources: Resources) -> None:

        self._read()
        tasks = []
        for task in self.select(selection):
            if task.state not in {'queued', 'running'}:
                self.tasks.remove(task)
            task = Task(task.cmd,
                        deps=task.deps,
                        resources=resources or task.resources,
                        folder=task.folder,
                        workflow=task.workflow,
                        restart=task.restart)
            tasks.append(task)
        self.submit(tasks, dry_run, read=False)

    def _read(self) -> None:
        if self.fname.is_file():
            data = json.loads(self.fname.read_text())
            for dct in data['tasks']:
                task = Task.fromdict(dct)
                self.tasks.append(task)
        else:
            fname = self.fname.with_name('slurm.json')
            if fname.is_file():
                data = json.loads(fname.read_text())
                for dct in data['jobs']:
                    task = Task.fromolddict(dct)
                    self.tasks.append(task)

        self.read_change_files()
        self.check()

    def read_change_files(self):
        paths = list(self.folder.glob('*-*-*'))
        files = []
        for path in paths:
            _, id, state = path.name.split('-')
            files.append((path.stat().st_ctime, int(id), state))
        states = {'0': 'running',
                  '1': 'done',
                  '2': 'FAILED',
                  '3': 'TIMEOUT'}
        for t, id, state in sorted(files):
            self.update(id, states[state], t)

        if files:
            self.changed = True

        for path in paths:
            path.unlink()

    def update(self,
               id: int,
               state: str,
               t: float = 0.0) -> None:

        if self.debug:
            print('UPDATE', id, state)

        for task in self.tasks:
            if task.id == id:
                break
        else:
            raise ValueError('No such task: {id}, {state}'
                             .format(id=id, state=state))

        t = t or time.time()

        task.state = state

        if state == 'done':
            for tsk in self.tasks:
                if task.dname in tsk.deps:
                    tsk.deps.remove(task.dname)
            task.write_done_file()
            task.tstop = t

        elif state == 'running':
            task.trunning = t

        elif state in ['FAILED', 'TIMEOUT']:
            for tsk in self.tasks:
                if task.dname in tsk.deps:
                    tsk.state = 'CANCELED'
                    tsk.tstop = t
            if state == 'FAILED':
                task.write_failed_file()
            task.tstop = t

        else:
            1 / 0

        if state != 'running':
            task.remove_empty_output_files()

        self.changed = True

    def check(self) -> None:
        t = time.time()

        for task in self.tasks:
            if task.state == 'running':
                delta = t - task.trunning - task.resources.tmax
                if delta > 0:
                    queue = self.queue(task)
                    if queue.timeout(task) or delta > 1800:
                        task.state = 'TIMEOUT'
                        task.remove_empty_output_files()
                        for tsk in self.tasks:
                            if task.dname in tsk.deps:
                                tsk.state = 'CANCELED'
                                tsk.tstop = t
                        self.changed = True

        bad = {task.dname for task in self.tasks if task.state.isupper()}
        for task in self.tasks:
            if task.state == 'queued':
                for dep in task.deps:
                    if dep in bad:
                        task.state = 'CANCELED'
                        task.tstop = t
                        self.changed = True
                        break

        for task in self.tasks:
            if task.state == 'FAILED':
                if not task.error:
                    oom = task.read_error()
                    if oom:
                        task.state = 'MEMORY'
                    self.changed = True

    def kick(self, dry_run: bool) -> None:
        self._read()
        tasks = []
        for task in self.tasks:
            if task.state in ['TIMEOUT', 'MEMORY'] and task.restart:
                task.resources.double(task.state)
                tasks.append(task)
        if tasks:
            tasks = self.find_depending(tasks)
            if dry_run:
                pprint(tasks)
            else:
                print('Restarting', plural(len(tasks), 'task'))
                for task in tasks:
                    self.tasks.remove(task)
                    task.error = ''
                self.submit(tasks, read=False)

    def _write(self):
        if self.debug:
            print('WRITE', len(self.tasks))
        text = json.dumps({'version': 2,
                           'tasks': [task.todict() for task in self.tasks]},
                          indent=2)
        self.fname.write_text(text)


def pjoin(folder, reldir):
    assert reldir == '.'
    return folder


def plural(n, thing):
    if n == 1:
        return '1 ' + thing
    return '{} {}s'.format(n, thing)


def colored(state: str) -> str:
    if state.isupper():
        return '\033[91m' + state + '\033[0m'
    if state.startswith('done'):
        return '\033[92m' + state + '\033[0m'
    return state


def pprint(tasks: List[Task],
           verbosity: int = 1,
           columns: str = 'ifnraste') -> None:

    if verbosity < 0:
        return

    if not tasks:
        return

    color = sys.stdout.isatty()
    home = str(Path.home())

    titles = ['id', 'folder', 'name', 'res.', 'age', 'state', 'time', 'error']
    c2i = {title[0]: i for i, title in enumerate(titles)}
    indices = [c2i[c] for c in columns]

    if verbosity:
        lines = [[titles[i] for i in indices]]
        lengths = [len(t) for t in lines[0]]
    else:
        lines = []
        lengths = [0] * len(columns)

    count = defaultdict(int)  # type: Dict[str, int]
    for task in tasks:
        words = task.words()
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
        lines[1:1] = [['-' * L for L in lengths]]
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
        count['total'] = len(tasks)
        print(', '.join('{}: {}'.format(state, n)
                        for state, n in count.items()))
