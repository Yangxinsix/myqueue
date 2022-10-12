"""Queue class for interacting with the queue.

File format versions:

5)  Changed from mod:func to mod@func.
6)  Relative paths.
8)  Type of Task.id changed from int to str.
9)  Added "user".
10) Switched to sqlite3.
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
from myqueue.selection import Selection

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
CREATE TABLE meta (
    key TEXT,
    value TEXT);
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
        self.lock = Lock(self.folder / 'queue.sqlite3.myqueue.lock',
                         timeout=10.0)
        self._connection: sqlite3.Connection | None = None

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
        if self._connection:
            self._connection.close()
        self.lock.release()

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection:
            return self._connection
        sqlfile = self.folder / 'queue.sqlite3'
        self._connection = sqlite3.connect(sqlfile)
        cur = self._connection.execute(
            'SELECT COUNT(*) FROM sqlite_master WHERE name="tasks"')

        if cur.fetchone()[0] == 0:
            self._initialize_db()
        else:
            version = int(
                self._connection.execute(
                    'SELECT value FROM meta where key="version"')
                .fetchone()[0])
            assert version <= VERSION
        return self._connection

    def get_tasks(self, selection: Selection = None) -> list[Task]:
        root = self.folder.parent
        sql = 'SELECT * FROM tasks'
        if selection:
            where, args = selection.sql_where_statement(root)
            if where:
                sql += f' WHERE {where}'
        else:
            args = []
        print(sql, args)
        with self.connection:
            tasks = []
            for row in self.connection.execute(sql, args):
                tasks.append(Task.from_sql_row(row, root))
        return tasks

    def _initialize_db(self) -> None:
        assert self.lock.locked
        with self.connection:
            for statement in INIT.split(';'):
                self.connection.execute(statement)
            self.connection.execute('INSERT INTO meta VALUES (?, ?)',
                                    ['version', str(VERSION)])

        jsonfile = self.folder / 'queue.json'
        if jsonfile.is_file():
            print(f'Converting {jsonfile} to SQLite3 file ...',
                  end='', flush=True)
            text = jsonfile.read_text()
            data = json.loads(text)
            root = self.folder.parent
            with self.connection:
                q = ', '.join('?' * 16)
                self.connection.executemany(
                    f'INSERT INTO tasks VALUES ({q})',
                    [Task.fromdict(dct, root).to_sql(root)
                     for dct in data['tasks']])
            jsonfile.with_suffix('.old.json').write_text(text)
            jsonfile.unlink()
            print(' done')

    def find_dependents(self, id: int) -> Iterator[Task]:
        """Yield dependents."""
        yield task ...
        yield from task.find_dependents(tasks)

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
