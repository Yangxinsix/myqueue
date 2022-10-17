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
import sys
import time
from pathlib import Path
from types import TracebackType
from typing import Iterator, Iterable

from myqueue.config import Configuration
from myqueue.schedulers import Scheduler, get_scheduler
from myqueue.states import State
from myqueue.task import Task
from myqueue.utils import Lock, cached_property
from myqueue.selection import Selection
from myqueue.migration import migrate

VERSION = 10

INIT = """\
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    folder TEXT,
    state CHARCTER,
    name TEXT,
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
CREATE TABLE dependencies (
    id INTEGER,
    did INTEGER,
    FOREIGN KEY (id) REFERENCES tasks(id),
    FOREIGN KEY (did) REFERENCES tasks(id));
CREATE TABLE meta (
    key TEXT,
    value TEXT);
CREATE INDEX folder_index on tasks(folder);
CREATE INDEX state_index on tasks(state);
CREATE INDEX dependincies_index1 on dependencies(id);
CREATE INDEX dependincies_index2 on dependencies(id)
"""


class Queue:
    """Object for interacting with your .myqueue/queue.sqlite3 file"""
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

        if self.lock.locked and not self.dry_run:
            self.process_change_files()
            self.check_for_timeout()
            self.check_for_oom()

        return self._connection

    def add(self, *tasks: Task) -> None:
        root = self.folder.parent
        q = ', '.join('?' * 17)
        with self.connection as con:
            con.executemany(
                f'INSERT INTO tasks VALUES ({q})',
                [task.to_sql(root) for task in tasks])
        deps = []
        for task in tasks:
            for dep in task.dtasks:
                deps.append((task.id, dep.id))
        con.executemany('INSERT INTO dependencies VALUES (?, ?)', deps)

    def sql(self,
            statement: str,
            args: list[str | int]) -> Iterator[tuple]:
        return self.connection.execute(statement, args)

    def select(self, selection: Selection = None) -> list[Task]:
        root = self.folder.parent
        if selection:
            where, args = selection.sql_where_statement(root)
        else:
            where = ''
            args = []
        return self.tasks(where, args)

    def tasks(self, where: str, args: list[str | int] = None) -> list[Task]:
        root = self.folder.parent
        if where:
            sql = f'SELECT * FROM tasks WHERE {where}'
        else:
            sql = 'SELECT * FROM tasks'
        print(sql, args)
        with self.connection:
            tasks = []
            for row in self.sql(sql, args or []):
                tasks.append(Task.from_sql_row(row, root))
        return tasks

    def _initialize_db(self) -> None:
        assert self.lock.locked
        with self.connection:
            for statement in INIT.split(';'):
                self.connection.execute(statement)
            self.sql('INSERT INTO meta VALUES (?, ?)',
                     ['version', str(VERSION)])

        jsonfile = self.folder / 'queue.json'
        if jsonfile.is_file():
            migrate(jsonfile, self.connection)

    def find_dependents(self,
                        ids: Iterable[int],
                        known: dict[int, list[int]] = None) -> Iterator[int]:
        """Yield dependents."""
        if known is None:
            known = {}
        result = set()
        for id in ids:
            if id in known:
                result.update(known[id])
            else:
                dependents = [
                    id for id, in self.sql(
                        'SELECT id FROM dependencies WHERE did = ?', [id])]
                known[id] = dependents
                result.update(dependents)
        if result:
            yield from result
            yield from self.find_dependents(result, known)

    def cancel_dependents(self, ids: Iterable[int]) -> None:
        t = time.time()
        with self.connection as con:
            con.executemany(
                'UPDATE tasks SET state = "C", tstop = ? WHERE id = ?',
                [(t, id) for id in self.find_dependents(ids)])

    def find_dependency(dname: TaskName,
                        current: dict[TaskName, Task],
                        new: dict[TaskName, Task],
                        force: bool = False) -> Task:
        """Convert dependency name to task."""
        if dname in current:
            task = current[dname]
            if task.state.is_bad():
                if force:
                    if dname not in new:
                        raise DependencyError(dname)
                    task = new[dname]
        elif dname in new:
            task = new[dname]
        else:
            raise DependencyError(dname)
        return task

    def remove(self, ids: Iterable[int]) -> None:
        self.cancel_dependents(ids)
        args = [[id] for id in ids]
        with self.connection as con:
            con.executemany('DELETE FROM dependencies WHERE id = ?', args)
            con.executemany('DELETE FROM dependencies WHERE did = ?', args)
            con.executemany('DELETE FROM tasks WHERE id = ?', args)

    def check_for_timeout(self) -> None:
        t = time.time()

        timeouts = []
        for task in self.tasks('state = "r"'):
            delta = t - task.trunning - task.resources.tmax
            if delta > 0:
                if self.scheduler.has_timed_out(task) or delta > 1800:
                    timeouts.append(task.id)

        with self.connection:
            self.connection.executemany(
                'UPDATE tasks SET state = "T", tstop = ? WHERE id = ?',
                [(t, id) for id in timeouts])
        self.cancel_dependents(timeouts)

    def check_for_oom(self) -> None:
        args = []
        for task in self.tasks('state = "F" AND error = ""'):
            oom = task.read_error_and_check_for_oom(self.scheduler)
            args.append(('M' if oom else 'F', task.error, task.id))
        with self.connection:
            self.connection.executemany(
                'UPDATE tasks SET state = ?, error = ? WHERE id = ?', args)

    def process_change_files(self) -> None:
        paths = list(self.folder.glob('*-*-*'))
        states = {0: State.running,
                  1: State.done,
                  2: State.FAILED,
                  3: State.TIMEOUT}
        files = []
        for path in paths:
            id, state = (int(x) for x in path.name.split('-')[1:])
            files.append((path.stat().st_ctime, id, state, path))

        for ctime, id, state, path in sorted(files):
            self.update_one_task(id, states[state], ctime, path)

    def update_one_task(self,
                        id: int,
                        newstate: State,
                        ctime: float,
                        path: Path) -> None:
        try:
            user, = self.sql('SELECT user FROM tasks WHERE id = ?', [id])
        except ValueError:
            print(f'No such task: {id}, {newstate}', file=sys.stderr)
            path.unlink()
            return None

        if user != self.config.user:
            return

        if newstate == 'done':
            with self.connection as con:
                con.execute('DELETE FROM dependencies WHERE did = ?', [id])
            with self.connection as con:
                con.execute(
                    'UPDATE tasks SET state = "d", tstop = ? WHERE id = ?',
                    [ctime, id])

        elif newstate == 'running':
            with self.connection as con:
                con.execute(
                    'UPDATE tasks SET state = "r", trunning = ? WHERE id = ?',
                    [ctime, id])

        else:
            assert newstate in ['FAILED', 'TIMEOUT', 'MEMORY']
            self.cancel_dependents([id])
            with self.connection as con:
                con.execute(
                    'UPDATE tasks SET state = ?, tstop = ? WHERE id = ?',
                    [newstate.value, ctime, id])

        path.unlink()


if __name__ == '__main__':
    from rich.table import Table
    from rich.console import Console
    prnt = Console().print
    name = sys.argv[1]
    db = sqlite3.connect(name)
    table = Table(title=name)
    columns = [line.strip().split()[0]
               for line in INIT.split(';')[0].splitlines()[1:]]
    for name in columns:
        table.add_column(name)
    for row in db.execute('SELECT * from tasks'):
        table.add_row(*[str(x) for x in row])
    prnt(table)

    table = Table(title='dependencies')
    table.add_column('id')
    table.add_column('did')
    for row in db.execute('SELECT * from dependencies'):
        table.add_row(*[str(x) for x in row])
    prnt(table)
