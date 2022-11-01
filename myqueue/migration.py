import json
from pathlib import Path
from sqlite3 import Connection

from myqueue.task import Task


def migrate(jsonfile: Path, con: Connection) -> None:
    print(f'Converting {jsonfile} to SQLite3 file ...',
          end='', flush=True)
    text = jsonfile.read_text()
    data = json.loads(text)
    root = jsonfile.parent.parent
    ids = {}
    tasks = []
    for dct in data['tasks']:
        task = Task.fromdict(dct, root)
        ids[task.dname] = task.id
        tasks.append(task)
    deps = []
    for task in tasks:
        for dep in task.deps:
            deps.append((task.id, ids[dep]))
    with con:
        q = ', '.join('?' * 17)
        con.executemany(
            f'INSERT INTO tasks VALUES ({q})',
            [task.to_sql(root) for task in tasks])
        con.executemany(
            'INSERT INTO dependencies VALUES (?, ?)', deps)
    jsonfile.with_suffix('.old.json').write_text(text)
    jsonfile.unlink()
    print(' done')
