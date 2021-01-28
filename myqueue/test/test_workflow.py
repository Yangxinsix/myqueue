from pathlib import Path
from myqueue.task import task
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


def test_workflow_old(mq):
    script = Path(__file__)
    mq(f'workflow {script}')
    