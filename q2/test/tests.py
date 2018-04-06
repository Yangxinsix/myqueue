import os
import sys
import tempfile
import time
from q2.cli import main


def q2(cmd):
    return main(cmd + ' --traceback')


tmpdir = tempfile.mkdtemp(prefix='q2-test-')


def wait(timeout=10.0):
    t0 = time.time()
    while q2('list -s qr -qq'):
        time.sleep(0.1)
        if time.time() - t0 > timeout:
            raise TimeoutError


def run_tests():
    print(tmpdir)
    os.chdir(tmpdir)
    os.environ['Q2_HOME'] = tmpdir

    q2('submit time.sleep+2')
    q2('submit echo+hello -d time.sleep+2')
    wait()
    for job in q2('list'):
        assert job.state == 'done'
    q2('submit q2.test.fail+2')
    q2('submit echo+hello -d q2.test.fail+2')
    wait()
    for job in q2('list'):
        print(job.state)
    q2('submit sleep+20@1x1s')
    q2('submit echo+hello -d sleep+20')
    wait()
    for job in q2('list'):
        print(job.state)
