from __future__ import annotations
import os

from myqueue.complete import complete, main
from myqueue.queue import Queue
from myqueue.task import create_task


def test_ls():
    words = complete('-', 'ls', 'mq ls -', 7)
    assert '--not-recursive' in words


def test_ls_main(capsys):
    main({'COMP_LINE': 'mq ls -', 'COMP_POINT': '7'}, '-', 'ls')
    out = capsys.readouterr().out
    words = out.splitlines()
    assert '--not-recursive' in words


def test_daemon():
    words = complete('', 'daemon', 'mq daemon ', 9)
    assert 'start' in words


def test_rm():
    words = complete('', 'mq', 'mq ', 3)
    assert 'rm' in words


def test_help():
    words = complete('', 'help', 'mq help ', 8)
    assert 'rm' in words
    assert 'remove' in words


def test_bare():
    words = complete('-', 'mq', 'mq -', 4)
    assert '-V' in words


def test_sync():
    words = complete('', 'sync', 'mq sync ', 8)
    assert words == []


def test_read(tmp_path):
    os.chdir(tmp_path)
    mq = tmp_path / '.myqueue'
    mq.mkdir()
    (mq / 'config.py').write_text('config = {"scheduler": "local"}\n')
    task = create_task('abc123')
    task.id = 117
    with Queue() as queue:
        queue.add(task)
    words = complete('', '-n', 'mq ls -n ', 9)
    assert words == ['abc123']
    words = complete('', '-i', 'mq ls -i ', 9)
    assert words == {'117'}
