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
    mq.wait()
    assert mq.states() == 'ddddddd'
    mq(f'workflow {script}')
    mq.wait()
    assert mq.states() == 'dddddddd'


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
    mq.wait()
    assert mq.states() == 'dddddd'


def test_direct_hello(tmp_path):
    os.chdir(tmp_path)
    Path('hello.sh').write_text('echo $@')
    hello()


def test_flow2(mq):
    script = Path(__file__).with_name('flow2.py')
    mq(f'workflow {script}')
    mq.wait()
    assert mq.states() == 'MCCC'
    mq('rm -sC .')
    mq(f'workflow {script}')
    assert mq.states() == 'M'
    mq(f'workflow {script} --force')
    mq.wait()
    assert mq.states() == 'MCCC'


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
    mq.wait()
    assert mq.states() == 'dd'
    mq('workflow wf.py .')
    assert mq.states() == 'dd'
    mq('rm -s d . -z')
    mq('rm -s d .')
    Path('shell:touch+hello.state').unlink()
    mq('workflow wf.py .')
    mq.wait()
    assert mq.states() == ''
    hello = Path('hello')
    hello.unlink()
    mq('workflow wf.py .')
    mq.wait()
    assert mq.states() == 'd'
    assert hello.is_file()


def test_workflow_running_only_with_targets(mq):
    Path('wf.py').write_text(wf)
    mq('workflow wf.py . -t shell:touch+hello')
    mq.wait()
    assert mq.states() == 'dd'


def test_workflow_with_failed_job(mq):
    Path('wf.py').write_text(wf)
    failed = Path('shell:sleep+3.state')
    failed.write_text('{"state": "FAILED"}\n')
    mq('workflow wf.py .')
    mq.wait()
    assert mq.states() == ''

    mq('workflow wf.py . --force --dry-run')
    mq.wait()
    assert mq.states() == ''
    assert failed.read_text() == '{"state": "FAILED"}\n'

    mq('workflow wf.py . --force')
    mq.wait()
    assert mq.states() == 'dd'
    assert failed.read_text() == '{"state": "done"}\n'


wf2 = """
from myqueue.task import task
def create_tasks(name, n):
    assert name == 'hello'
    assert n == 5
    return [task('shell:echo+hi', diskspace=1) for _ in range(4)]
"""


def test_workflow2(mq):
    Path('wf2.py').write_text(wf2)
    mq('workflow wf2.py . -a name=hello,n=5')
    mq('kick')
    assert mq.states() == 'hhqq'
    mq.wait()
    mq('kick')
    mq.wait()
    assert mq.states() == 'dddd'


def test_failing_scheduler(mq):
    with pytest.raises(RuntimeError):
        # Special argument that makes test-scheduler raise an error:
        mq('submit "time.sleep FAIL"')
    mq.wait()
    assert mq.states() == ''


wf3 = """
from myqueue.task import task
def create_tasks():
    return [task('shell:echo+hi'),
            task('shell:echo+FAIL')]
"""


def test_workflow3(mq):
    Path('wf3.py').write_text(wf3)
    with pytest.raises(RuntimeError):
        mq('workflow wf3.py')
    mq.wait()
    assert mq.states() == 'd'
