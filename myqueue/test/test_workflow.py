import os
from pathlib import Path
from myqueue.task import task
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
