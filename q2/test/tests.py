import os
import tempfile
import time
from pathlib import Path

from q2.cli import main


def q2(cmd):
    args = cmd.split()
    args[1:1] = ['--traceback']
    return main(args)


all_tests = {}


def test(func):
    all_tests[func.__name__] = func
    return func


def states():
    return ''.join(job.state[0] for job in q2('list'))


tmpdir = tempfile.mkdtemp(prefix='q2-test-')


def wait(timeout: float = 10.0)-> None:
    t0 = time.time()
    while q2('list -s qr -qq'):
        time.sleep(0.1)
        if time.time() - t0 > timeout:
            raise TimeoutError


def run_tests(tests):
    print('Running tests in', tmpdir)
    os.chdir(tmpdir)
    os.environ['Q2_HOME'] = tmpdir
    os.environ['Q2_DEBUG'] = 'yes!'

    if not tests:
        tests = list(all_tests)

    for name in tests:
        print('\n::::::::::::::::::::::::: Running "{}" test:\n'.format(name))
        all_tests[name]()
        for f in Path(tmpdir).glob('**/*'):
            f.unlink()


@test
def submit():
    q2('submit time.sleep+2')
    q2('submit echo+hello -d time.sleep+2')
    wait()
    for job in q2('list'):
        assert job.state == 'done'


@test
def fail():
    q2('submit q2.test.fail+2')
    q2('submit echo+hello -d q2.test.fail+2')
    wait()
    assert states() == 'FC'
    q2('resubmit -sF .')
    wait()
    assert states() == 'CF'


@test
def timeout():
    q2('submit sleep+3@1x1s')
    q2('submit echo+hello -d sleep+3')
    wait()
    q2('resubmit -sT . -R 1x5s')
    wait()
    assert states() == 'Cd'


wf = """
from q2.job import Job
def workflow():
    j1 = Job('sleep+3')
    return [j1, Job('echo+hello', deps=[j1])]
"""


@test
def workflow():
    q2('submit sleep+3@1x1m -w')
    time.sleep(2)
    Path('wf.py').write_text(wf)
    q2('workflow wf.py .')
    wait()
    assert states() == 'dd'
