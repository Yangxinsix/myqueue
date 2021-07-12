import os
import sys
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
    time.sleep(1)
    yield scheduler
    scheduler.send('stop')
    thread.join()
    os.chdir(dir)


@pytest.mark.skipif(sys.version_info < (3, 8),
                    reason='requires Python 3.8 or higher')
def test_local_scheduler(scheduler):
    task1 = create_task('shell:sleep+10', tmax='1s')
    scheduler.submit(task1)
    task2 = create_task('shell:sleep+5')
    scheduler.submit(task2)
    ids = scheduler.get_ids()
    assert ids == [1, 2]
    scheduler.cancel(task2)
    ids = scheduler.get_ids()
    assert ids == [1]
