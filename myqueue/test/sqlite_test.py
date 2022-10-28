import json
import os

from myqueue.queue import Queue, dump_db
from myqueue.task import create_task


def test_migration(tmp_path):
    os.chdir(tmp_path)
    mq = tmp_path / '.myqueue'
    mq.mkdir()
    task = create_task('time@sleep')
    dct = {'tasks': [task.todict()]}
    text = json.dumps(dct)
    (mq / 'queue.json').write_text(text)
    with Queue() as q:
        tasks = q.select()
        assert len(tasks) == 1
    dump_db(mq / 'queue.sqlite3')
