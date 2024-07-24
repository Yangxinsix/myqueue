from __future__ import annotations
import os
import threading
import time
from pathlib import Path

import pytest

from myqueue.config import Configuration
from myqueue.schedulers.local import LocalScheduler, Server
from myqueue.submitting import submit_tasks
from myqueue.task import create_task
from myqueue.workflow import collect, run
from myqueue.queue import sort_out_dependencies, Queue


@pytest.fixture(scope='function')
def scheduler(tmpdir):
    port = 39998
    dir = os.getcwd()
    home = Path(tmpdir)
    (home / '.myqueue').mkdir()
    config = Configuration('local', home=home)
    os.chdir(tmpdir)
    server = Server(config, port=port)
    thread = threading.Thread(target=server.run)
    thread.start()
    scheduler = LocalScheduler(config)
    import time
    time.sleep(0.5)
    scheduler.port = server.port
    yield scheduler, config
    scheduler.send('stop')
    thread.join()
    os.chdir(dir)


def test_local_scheduler_000(scheduler):
    scheduler, config = scheduler
    task1 = create_task('shell:echo', tmax='1s')
    i1 = scheduler.submit(task1)
    assert i1 == 1
    task2 = create_task('shell:echo')
    i2 = scheduler.submit(task2)
    task1.id = i1
    task2.id = i2
    print(i1, i2)
    q = Queue(config)
    with q:
        q.add(task1, task2)
    while ids := scheduler.get_ids():
        print(ids)
    q = Queue(config)
    with q:
        print('QQQQQQQQQ', q)
        for t in q.tasks(''):
            print('TASK:', t)


def test_local_scheduler(scheduler):
    scheduler, config = scheduler
    task1 = create_task('shell:sleep+10', tmax='1s')
    i1 = scheduler.submit(task1)
    assert i1 == 1
    task2 = create_task('shell:sleep+5')
    scheduler.submit(task2)
    ids = scheduler.get_ids()
    assert ids == [1, 2]
    scheduler.cancel(2)
    ids = scheduler.get_ids()
    assert ids == [1]


def workflow():
    with run(shell='fail1', name='1'):
        run(shell='echo', name='2')
    with run(shell='fail2', name='3'):
        run(shell='echo', name='4')


def test_local_scheduler3(scheduler):
    scheduler, config = scheduler
    tasks = collect(workflow, Path())
    sort_out_dependencies(tasks)
    ids, ex = submit_tasks(scheduler,
                           tasks,
                           verbosity=2,
                           dry_run=False)
    assert len(ids) == 4
    assert ex is None
    for i in range(10):
        if len(scheduler.get_ids()) == 0:
            break
        time.sleep(0.1)
    else:  # no break
        1 / 0
    names = set(path.name[6:]
                for path in Path('.myqueue').glob('local-*-?'))
    assert names == set(['1-2', '3-2', '3-0', '1-0'])
