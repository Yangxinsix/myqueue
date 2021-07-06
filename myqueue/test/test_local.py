import os
import threading
from pathlib import Path

import pytest

from myqueue.config import Configuration
from myqueue.local import LocalScheduler, Server
from myqueue.task import task as create_task


@pytest.fixture(scope='function')
def scheduler(tmpdir):
    dir = os.getcwd()
    home = Path(tmpdir)
    (home / '.myqueue').mkdir()
    config = Configuration('local', home=home)
    os.chdir(tmpdir)
    server = Server(config, port=39998)
    thread = threading.Thread(target=server.start)
    thread.start()
    scheduler = LocalScheduler(config)
    scheduler.port = 39998
    import time
    print('AAAA1')
    time.sleep(1)
    print('AAAA2')
    yield scheduler
    print('AAAA3')
    scheduler.send('stop')
    print('AAAA4')
    thread.join()
    os.chdir(dir)


def test_local_scheduler(scheduler):
    print('hello')
    task = create_task('shell:sleep+10', tmax='1s')
    scheduler.submit(task)
    ids = scheduler.get_ids()
    assert ids == [1]
