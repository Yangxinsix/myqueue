import json
from pathlib import Path
from sqlite3 import Connection

from myqueue.task import Task


def migrate(jsonfile: Path, con: Connection) -> None:
    """Migrate queue from version 9 to 11."""
    text = jsonfile.read_text()

    try:
        data = json.loads(text)
    except json.decoder.JSONDecodeError:
        return

    root = jsonfile.parent.parent

    print(f'Converting {jsonfile} to SQLite3 file ...',
          end='', flush=True)

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

    # Make sure old daemons crash:
    jsonfile.write_text('Moved to queue.old.json\n')

    print(' done')
