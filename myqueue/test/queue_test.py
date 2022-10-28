import os

from myqueue.queue import Queue


def test_no_such_task(tmp_path):
    os.chdir(tmp_path)
    mq = tmp_path / '.myqueue'
    mq.mkdir()
    p = mq / 'test-42-2'
    p.write_text('')
    with Queue() as q:
        q.connection  # this will trigger q.update_one_task()
    assert not p.is_file()
