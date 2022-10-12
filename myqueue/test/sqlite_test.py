import json
import os

from myqueue.queue import Queue
from myqueue.task import task as create_task


def test_migration(tmp_path):
    os.chdir(tmp_path)
    q = Queue()
    mq = tmp_path / '.myqueue'
    mq.mkdir()
    task = create_task('time@sleep')
    dct = {'tasks': [task.todict()]}
    text = json.dumps(dct)
    (mq / 'queue.json').write_text(text)
    con = q.connection()
