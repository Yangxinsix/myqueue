"""Queue class for interacting with the queue.

File format versions:

5)  Changed from mod:func to mod@func.
6)  Relative paths.
8)  Type of Task.id changed from int to str.
9)  Added "user".
10) ...
"""
from __future__ import annotations

import json
import time
from collections import defaultdict
from functools import cached_property
from pathlib import Path
from types import TracebackType

from myqueue.config import Configuration
from myqueue.scheduler import Scheduler, get_scheduler
from myqueue.states import State
from myqueue.task import Task
from myqueue.utils import Lock

VERSION = 10


class Queue:
    """Object for interacting with the scheduler."""
    def __init__(self,
                 config: Configuration,
                 need_lock: bool = True,
                 dry_run: bool = False):
        self.need_lock = need_lock
        self.config = config
        self.folder = config.home / '.myqueue'
        self.lock = Lock(self.folder / 'queue.json.lock',
                         timeout=10.0)
        self.tasks: list[Task] = []

    @cached_property
    def scheduler(self) -> Scheduler:
        """Scheduler object."""
        return get_scheduler(self.config)

    def __enter__(self) -> Queue:
        if self.need_lock:
            self.lock.acquire()
        else:
            try:
                self.lock.acquire()
            except PermissionError:
                pass  # it's OK to try to read without beeing able to write
        return self

    def __exit__(self,
                 type: Exception,
                 value: Exception,
                 tb: TracebackType) -> None:
        if self.changed:
            assert self.lock.locked
            self._write()
        self.lock.release()

    def find_depending(self, tasks: list[Task]) -> list[Task]:
        """Generate list of tasks including dependencies."""
        map = {task.dname: task for task in self.tasks}
        d: dict[Task, list[Task]] = defaultdict(list)
        for task in self.tasks:
            for dname in task.deps:
                tsk = map.get(dname)
                if tsk:
                    d[tsk].append(task)

        removed = []

        def remove(task: Task) -> None:
            removed.append(task)
            for j in d[task]:
                remove(j)

        for task in tasks:
            remove(task)

        return sorted(set(removed), key=lambda task: task.id)

    def _read(self) -> None:
        q = self.folder / 'queue.json'
        if q.is_file():
            data = json.loads(q.read_text())
            root = self.folder.parent
            for dct in data['tasks']:
                task = Task.fromdict(dct, root)
                self.tasks.append(task)

        if self.lock.locked:
            self.read_change_files()
            self.check()

    def read_change_files(self) -> None:
        paths = list(self.folder.glob('*-*-*'))
        files = []
        for path in paths:
            _, id, state = path.name.split('-')
            files.append((path.stat().st_ctime, id, state, path))
        states = {'0': State.running,
                  '1': State.done,
                  '2': State.FAILED,
                  '3': State.TIMEOUT}
        for t, id, state, path in sorted(files):
            self.update(id, states[state], t, path)

    def update(self,
               id: str,
               state: State,
               t: float,
               path: Path) -> None:

        for task in self.tasks:
            if task.id == id:
                break
        else:  # no break
            print(f'No such task: {id}, {state}')
            path.unlink()
            return

        if task.user != self.config.user:
            return

        t = t or time.time()

        task.state = state

        if state == 'done':
            for tsk in self.tasks:
                if task.dname in tsk.deps:
                    tsk.deps.remove(task.dname)
            task.write_state_file()
            task.tstop = t

        elif state == 'running':
            task.trunning = t

        elif state in ['FAILED', 'TIMEOUT', 'MEMORY']:
            task.cancel_dependents(self.tasks, t)
            task.tstop = t
            task.write_state_file()

        else:
            raise ValueError(f'Bad state: {state}')

        if state != 'running':
            mem = self.scheduler.maxrss(id)
            task.memory_usage = mem

        self.changed.add(task)
        path.unlink()

    def check(self) -> None:
        t = time.time()

        for task in self.tasks:
            if task.state == 'running':
                delta = t - task.trunning - task.resources.tmax
                if delta > 0:
                    if self.scheduler.has_timed_out(task) or delta > 1800:
                        task.state = State.TIMEOUT
                        task.tstop = t
                        task.cancel_dependents(self.tasks, t)
                        self.changed.add(task)

        bad = {task.dname for task in self.tasks if task.state.is_bad()}
        for task in self.tasks:
            if task.state == 'queued':
                for dep in task.deps:
                    if dep in bad:
                        task.state = State.CANCELED
                        task.tstop = t
                        self.changed.add(task)
                        break

        for task in self.tasks:
            if task.state == 'FAILED':
                if not task.error:
                    oom = task.read_error(self.scheduler)
                    if oom:
                        task.state = State.MEMORY
                        task.write_state_file()
                    self.changed.add(task)

    def _write(self) -> None:
        root = self.folder.parent
        dicts = []
        for task in self.tasks:
            dicts.append(task.todict(root))

        text = json.dumps(
            {'version': VERSION,
             'warning': 'Do NOT edit this file!',
             'unless': 'you know what you are doing.',
             'tasks': dicts},
            indent=2)
        self.fname.write_text(text)
