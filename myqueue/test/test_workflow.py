from pathlib import Path
from myqueue.task import task
from myqueue.workflow import workflow_from_function


def create_tasks():
    return [task('somepackage.somemodule')]


def test_basic_workflow():
    tasks = workflow_from_function(
        workflow_function=create_tasks,
        folders=[Path('.')])

    assert tasks[0].todict() == task('somepackage.somemodule',
                                     workflow=True).todict()
