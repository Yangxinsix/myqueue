"""Queue class for interacting with the queue.

File format versions:

5)  Changed from mod:func to mod@func.
6)  Relative paths.
8)  Type of Task.id changed from int to str.
9)  Added "user".
10) ...
"""
from __future__ import annotations

import sqlite3
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from types import TracebackType

from myqueue.config import Configuration
from myqueue.schedulers import Scheduler, get_scheduler
from myqueue.states import State
from myqueue.task import Task
from myqueue.utils import Lock, cached_property

VERSION = 10

INIT = """\
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  folder TEXT,
  state CHARCTER,
  cmd TEXT,
  resources TEXT,
  restart INTEGER,
  workflow INTEGER,
  deps TEXT,
  diskspace INTEGER,
  notifications TEXT,
  creates TEXT,
  tqueued REAL,
  trunning REAL,
  tstop REAL,
  error TEXT,
  user TEXT);
CREATE TABLE information (
    version INTEGER);
CREATE INDEX folder_index on tasks(folder);
CREATE INDEX state_index on tasks(state)
"""


class Queue:
    """Object for interacting with your .myqueue/queue.json file"""
    def __init__(self,
                 config: Configuration = None,
                 *,
                 need_lock: bool = True,
                 dry_run: bool = False):
        self.need_lock = need_lock
        self.dry_run = dry_run
        self.config = config or Configuration('test')
        self.folder = self.config.home / '.myqueue'
        self.lock = Lock(self.folder / 'queue.json.lock',
                         timeout=10.0)

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

    @cached_property
    def connection(self) -> sqlite3.Connection:
        sqlfile = self.folder / 'queue.sqlite3'
        con = sqlite3.connect(sqlfile)
        cur = con.execute(
            'SELECT COUNT(*) FROM sqlite_master WHERE name="tasks"')

        if cur.fetchone()[0] == 0:
            self._initialize_db(con)
        else:
            version = int(
                con.execute(
                    'SELECT value FROM information WHERE name="version"')
                .fetchone()[0])
            assert version <= VERSION
        return con

    def _initialize_db(self, con: sqlite3.Connection) -> None:
        with con:
            for statement in INIT.split(';'):
                con.execute(statement)
            con.execute('INSERT INTO information VALUES (?)', [VERSION])

        jsonfile = self.folder / 'queue.json'
        if jsonfile.is_file():
            print(f'Converting {jsonfile} to SQLite3 file ...', end='')
            text = jsonfile.read_text()
            data = json.loads(text)
            root = self.folder.parent
            with con:
                q = ', '.join('?' * 16)
                con.executemany(
                    f'INSERT INTO tasks VALUES ({q})',
                    (Task.fromdict(dct, root).to_sql()
                     for dct in data['tasks']))
            jsonfile.with_suffix('.old.json').write_text(text)
            jsonfile.unlink()
            print(' done')

    def __exit__(self,
                 type: Exception,
                 value: Exception,
                 tb: TracebackType) -> None:
        if self.changed and not self.dry_run:
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

    def _read_tasks(self) -> list[Task]:
        if self.lock.locked and not self.dry_run:
            read_change_files(self.folder, self.config.user)
            check(self.scheduler)


def read_change_files(folder: Path,
                      tasks: list[Task],
                      user: str) -> set[Task]:
    paths = list(folder.glob('*-*-*'))
    files = []
    for path in paths:
        _, id, state = path.name.split('-')
        files.append((path.stat().st_ctime, id, state, path))
    states = {'0': State.running,
              '1': State.done,
              '2': State.FAILED,
              '3': State.TIMEOUT}
    changed = set()
    for t, id, state, path in sorted(files):
        task = update(tasks, id, states[state], t, path, user)
        if task:
            changed.add(task)
    return changed


def update(tasks: list[Task],
           id: str,
           state: State,
           t: float,
           path: Path,
           user: str) -> None | Task:

    for task in tasks:
        if task.id == id:
            break
    else:  # no break
        print(f'No such task: {id}, {state}', file=sys.stderr)
        path.unlink()
        return None

    if task.user != user:
        return None

    t = t or time.time()

    task.state = state

    if state == 'done':
        for tsk in tasks:
            if task.dname in tsk.deps:
                tsk.deps.remove(task.dname)
        task.tstop = t

    elif state == 'running':
        task.trunning = t

    else:
        assert state in ['FAILED', 'TIMEOUT', 'MEMORY']
        task.cancel_dependents(tasks, t)
        task.tstop = t

    path.unlink()
    return task


def check(tasks: list[Task], scheduler: Scheduler) -> set[Task]:
    t = time.time()

    changed = set()

    for task in tasks:
        if task.state == 'running':
            delta = t - task.trunning - task.resources.tmax
            if delta > 0:
                if scheduler.has_timed_out(task) or delta > 1800:
                    task.state = State.TIMEOUT
                    task.tstop = t
                    task.cancel_dependents(tasks, t)
                    changed.add(task)

    bad = {task.dname for task in tasks if task.state.is_bad()}
    for task in tasks:
        if task.state == 'queued':
            for dep in task.deps:
                if dep in bad:
                    task.state = State.CANCELED
                    task.tstop = t
                    changed.add(task)
                    break

    for task in tasks:
        if task.state == 'FAILED':
            if not task.error:
                oom = task.read_error(scheduler)
                if oom:
                    task.state = State.MEMORY
                changed.add(task)
    return changed
