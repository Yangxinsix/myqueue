"""Queue class for interacting with the queue.

File format versions:

5)  Changed from mod:func to mod@func.
6)  Relative paths.
8)  Type of Task.id changed from int to str.
9)  Added "user".
10) Switched to sqlite3.
11) Renamed diskspace to weight.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path
from types import TracebackType
from typing import Iterator, Iterable, Sequence
from typing_extensions import LiteralString

from myqueue.config import Configuration
from myqueue.schedulers import Scheduler, get_scheduler
from myqueue.states import State
from myqueue.task import Task, create_task
from myqueue.utils import Lock, cached_property, normalize_folder
from myqueue.selection import Selection
from myqueue.migration import migrate

VERSION = 11

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
    weight REAL,
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
CREATE INDEX dependincies_index2 on dependencies(did)
"""


class DependencyError(Exception):
    """Bad dependency."""


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
        """Get or create a connection object."""
        if self._connection:
            return self._connection
        sqlfile = self.folder / 'queue.sqlite3'
        if self.lock.locked:
            self._connection = sqlite3.connect(sqlfile)
        else:
            self._connection = sqlite3.connect(f'file:{sqlfile}?mode=ro',
                                               uri=True)
        cur = self._connection.execute(
            'SELECT COUNT(*) FROM sqlite_master WHERE name="tasks"')

        if cur.fetchone()[0] == 0:
            self._initialize_db()
        else:
            version = int(
                self._connection.execute(
                    'SELECT value FROM meta where key="version"')
                .fetchone()[0])
            assert 11 <= version <= VERSION

        if self.lock.locked and not self.dry_run:
            self.process_change_files()
            self.check_for_timeout()
            self.check_for_oom()

        return self._connection

    def add(self, *tasks: Task) -> None:
        """Add tasks to database."""
        deps = []
        for task in tasks:
            for dep in task.dtasks:
                deps.append((task.id, dep.id))

        root = self.folder.parent
        q = ', '.join('?' * 17)
        with self.connection as con:
            con.executemany(
                f'INSERT INTO tasks VALUES ({q})',
                [task.to_sql(root) for task in tasks])
            con.executemany('INSERT INTO dependencies VALUES (?, ?)', deps)

    def sql(self,
            statement: LiteralString,
            args: list[str | int] = None) -> Iterator[tuple]:
        """Raw SQL execution."""
        return self.connection.execute(statement, args or [])

    def select(self, selection: Selection = None) -> list[Task]:
        """Create tasks from selection object."""
        root = self.folder.parent
        if selection:
            where, args = selection.sql_where_statement(root)
        else:
            where = ''
            args = []
        return self.tasks(where, args)

    def tasks(self,
              where: LiteralString,
              args: list[str | int] = None) -> list[Task]:
        """Create tasks from SQL WHERE statement."""
        root = self.folder.parent
        if where:
            sql = f'SELECT * FROM tasks WHERE {where}'
        else:
            sql = 'SELECT * FROM tasks'
        with self.connection:
            tasks = []
            for row in self.sql(sql, args or []):
                tasks.append(Task.from_sql_row(row, root))
        return tasks

    def _initialize_db(self) -> None:
        """Initialize tables and write version number."""
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
        """Set state of dependents to CANCELED."""
        if self.dry_run:
            return
        t = time.time()
        args = [(t, id) for id in self.find_dependents(ids)]
        with self.connection as con:
            con.executemany(
                'UPDATE tasks SET state = "C", tstop = ? WHERE id = ?', args)

    def remove(self, ids: Iterable[int]) -> None:
        """Remove tasks."""
        if self.dry_run:
            return
        ids = list(ids)
        self.cancel_dependents(ids)
        args = [[id] for id in ids]
        with self.connection as con:
            con.executemany('DELETE FROM dependencies WHERE id = ?', args)
            con.executemany('DELETE FROM dependencies WHERE did = ?', args)
            con.executemany('DELETE FROM tasks WHERE id = ?', args)

    def check_for_timeout(self) -> None:
        """Find "running" tasks that are actually timed out."""
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
        """Fin out-of-memory tasks."""
        args = []
        for task in self.tasks('state = "F" AND error = ""'):
            oom = task.read_error_and_check_for_oom(self.scheduler)
            args.append(('M' if oom else 'F', task.error, task.id))
        with self.connection:
            self.connection.executemany(
                'UPDATE tasks SET state = ?, error = ? WHERE id = ?', args)

    def process_change_files(self) -> None:
        """Process state-change files from running tasks."""
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
        """Update single task."""
        try:
            (user,), = self.sql('SELECT user FROM tasks WHERE id = ?', [id])
        except ValueError:
            print(f'No such task: {id}, {newstate}', file=sys.stderr)
            path.unlink()
            return

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


def sort_out_dependencies(tasks: Sequence[Task],
                          queue: Queue = None,
                          done: list[Task] = None) -> None:
    """Get dependencies ready for submitting."""
    root = queue.config.home if queue is not None else Path('.').absolute()

    name_to_task = {str(task.dname.relative_to(root)): task
                    for task in tasks}

    name_to_id_and_state: dict[str, tuple[int, str]] = {}

    if done is not None:
        for task in done:
            name_to_id_and_state[str(task.dname.relative_to(root))] = (0, 'd')

    for task in tasks:
        task.dtasks = []
        deps = []
        for dname in task.deps:
            name = str(dname.relative_to(root))
            dtask = name_to_task.get(name)
            if dtask is None:
                id, state = name_to_id_and_state.get(name, (-1, ''))
                if id == -1:
                    assert queue is not None
                    rows = queue.sql(
                        'SELECT id, state FROM tasks '
                        'WHERE name = ? AND folder = ?',
                        [dname.name, normalize_folder(task.folder, root)])
                    id, state = max(rows, default=(-1, ''))
                    if id == -1:
                        raise DependencyError(f"Can't find {name}")
                    name_to_id_and_state[name] = id, state
                if state in 'qhr':
                    dtask = create_task('dummy')
                    dtask.id = id
                    dtask.state = State(state)
                elif state == 'd':
                    continue
                else:
                    raise DependencyError(f'Bad state ({state}): {name}')

            task.dtasks.append(dtask)
            deps.append(dname)
        task.deps = deps


def dump_db(path: Path) -> None:
    """Pretty-print content of sqlite3 db file."""
    from rich.table import Table
    from rich.console import Console
    prnt = Console().print
    db = sqlite3.connect(path)
    table = Table(title=str(path))
    columns = [line.strip().split()[0]
               for line in INIT.split(';', maxsplit=1)[0].splitlines()[1:]]
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

    table = Table(title='meta')
    table.add_column('key')
    table.add_column('value')
    for row in db.execute('SELECT * from meta'):
        table.add_row(*[str(x) for x in row])
    prnt(table)


if __name__ == '__main__':
    dump_db(Path(sys.argv[1]))
