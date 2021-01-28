import os
from pathlib import Path
from myqueue.task import task
from myqueue.workflow import run
from myqueue.test.flow1 import workflow
# from myqueue.workflow import workflow_from_function


def create_tasks():
    return [task('somepackage.somemodule')]


def xxxtest_basic_workflow():
    """
    tasks = workflow_from_function(
        workflow_function=create_tasks,
        folders=[Path('.')])

    assert tasks[0].todict() == task('somepackage.somemodule',
                                     workflow=True).todict()
    """
    pass


def test_flow1(mq):
    script = Path(__file__).with_name('flow1.py')
    mq(f'workflow {script}')
    mq.wait()
    assert mq.states() == 'dddd'
    mq(f'workflow {script}')
    mq.wait()
    assert mq.states() == 'ddddd'


def test_flow1_direct():
    a = workflow(lambda func, **kwargs: func)
    assert a == 3


def test_flow1_direct_cached(tmp_path, capsys):
    os.chdir(tmp_path)
    a = workflow(run)
    assert a == 3
    assert capsys.readouterr().out == '0\n1\n2\n(1, 2, 3)\n3\n'
    workflow(run)
    assert capsys.readouterr().out == ''


def test_workflow_old(mq):
    script = Path(__file__)
    mq(f'workflow {script}')
