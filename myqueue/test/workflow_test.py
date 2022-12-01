from __future__ import annotations

import os
from pathlib import Path
import time

import pytest
from myqueue.test.flow1 import workflow
from myqueue.test.hello import workflow as hello


def test_flow1(mq):
    script = Path(__file__).with_name('flow1.py')

    mq(f'workflow {script}')
    assert mq.wait() == 'd' * 7

    mq(f'workflow {script}')
    assert mq.wait() == 'd' * 8

    mq('rm -sd')
    assert mq.wait() == 'd' * 8

    mq('rm -sd --force')
    assert mq.wait() == ''

    mq(f'workflow {script}')
    assert mq.wait() == ''

    Path('builtins.print.result').unlink()
    mq(f'workflow {script}')
    assert mq.wait() == 'd'


def test_direct_cached_flow1(tmp_path, capsys):
    os.chdir(tmp_path)
    a = workflow()
    assert a == 3
    assert capsys.readouterr().out == '\n'.join('0213243') + '\n'
    workflow()
    assert capsys.readouterr().out == ''


def test_workflow_old(mq):
    script = Path(__file__)
    mq(f'workflow {script}')


def test_hello(mq):
    Path('hello.sh').write_text('echo $@')
    script = Path(__file__).with_name('hello.py')
    mq(f'workflow {script}')
    assert mq.wait() == 'dddddd'


def test_direct_hello(tmp_path):
    os.chdir(tmp_path)
    Path('hello.sh').write_text('echo $@')
    hello()


def test_flow2(mq):
    script = Path(__file__).with_name('flow2.py')
    mq(f'workflow {script}')
    assert mq.wait() == 'MCCC'
    mq('rm -sC . --force')
    mq(f'workflow {script}', error=1)
    assert mq.states() == 'M'
    mq(f'workflow {script} --force')
    assert mq.wait() == 'MCCC'


wf = """
from myqueue.task import task
def create_tasks():
    t1 = task('shell:sleep+3')
    t2 = task('shell:touch+hello', deps=[t1], creates=['hello'])
    return [t1, t2]
"""


def test_workflow(mq):
    mq('submit shell:sleep+3 -R1:1m -w')
    time.sleep(2)
    Path('wf.py').write_text(wf)
    mq('workflow wf.py . -t shell:touch+hello')
    assert mq.wait() == 'dd'
    mq('workflow wf.py .')
    assert mq.states() == 'dd'
    mq('rm -i 2 -z')  # dry-run
    mq('rm -i 2')  # needs --force
    assert mq.states() == 'dd'
    mq('rm -i 2 --force')
    mq('workflow wf.py .')
    assert mq.wait() == 'd'
    hello = Path('hello')
    hello.unlink()
    mq('workflow wf.py .')
    assert mq.wait() == 'dd'
    assert hello.is_file()


def test_workflow_running_only_with_targets(mq):
    Path('wf.py').write_text(wf)
    mq('workflow wf.py . -t shell:touch+hello')
    assert mq.wait() == 'dd'


def test_workflow_with_failed_job(mq):
    # Introduce bug in workflow task:
    Path('wf.py').write_text(wf.replace('+3', '+a'))
    mq('workflow wf.py .')
    assert mq.wait() == 'FC'

    # Fix bug:
    Path('wf.py').write_text(wf)
    mq('workflow wf.py . --force --dry-run')
    assert mq.wait() == 'FC'

    mq('workflow wf.py . --force')
    assert mq.wait() == 'Fdd'


wf2 = """
from myqueue.task import task
def create_tasks(name, n):
    assert name == 'hello'
    assert n == 5
    return [task('shell:echo+hi', name=f'x{i}', weight=1) for i in range(4)]
"""


def test_workflow2(mq):
    Path('wf2.py').write_text(wf2)
    mq('workflow wf2.py . -a name=hello,n=5')
    mq('kick')
    assert mq.states() == 'hhqq'
    mq.wait()
    mq('kick')
    assert mq.wait() == 'dddd'


wf2_new = """
from myqueue.workflow import run
def workflow():
    for i in range(4):
        run(shell='echo', args=['hi'], name=f'x{i}', weight=1)
"""


def test_workflow2_new(mq):
    Path('wf2.py').write_text(wf2_new)
    mq('workflow wf2.py')
    mq('kick')
    assert mq.states() == 'hhqq'
    mq.wait()
    mq('kick')
    assert mq.wait() == 'dddd'


def test_failing_scheduler(mq):
    with pytest.raises(RuntimeError):
        # Special argument that makes test-scheduler raise an error:
        mq('submit "time.sleep FAIL"')
    assert mq.wait() == ''


wf3 = """
from myqueue.task import task
def create_tasks():
    return [task('shell:echo+hi'),
            task('shell:echo+FAIL')]
"""


def test_workflow3(mq):
    Path('wf3.py').write_text(wf3)
    mq('workflow wf3.py', error=1)
    assert mq.wait() == 'd'


wf4 = """
from myqueue.workflow import run
def workflow():
    with run(function=lambda: None, name='A'):
        run(function=lambda: None, name='B')
"""


def test_workflow_depth_first(mq):
    """Order should be 1/A, 1/B, 2/A, 2/B and not 1/A, 2/A, 1/B, 2/B."""
    Path('wf4.py').write_text(wf4)
    Path('1').mkdir()
    Path('2').mkdir()
    mq('workflow wf4.py 1 2')
    assert mq.wait() == 'dddd'
    assert Path('1/B.2.out').is_file()


wf5 = """
from myqueue.workflow import run
def workflow():
    run(function=lambda: None, name='A')
    run(function=lambda: None, name='A')
"""


def test_workflow_repeated_name(mq):
    Path('wf5.py').write_text(wf5)
    mq('workflow wf5.py', error=1)


wf_creates = """
from myqueue.workflow import run
def workflow():
    with run(shell='echo', creates=['out.txt']):
        run(function=print)
"""


def test_creates(mq):
    Path('wf.py').write_text(wf_creates)
    Path('out.txt').write_text('OK\n')
    mq('workflow wf.py')
    assert mq.wait() == 'd'
