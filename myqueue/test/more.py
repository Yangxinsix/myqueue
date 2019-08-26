from .testrunner import test, wait, states


@test
def completion():
    from myqueue.utils import update_completion
    update_completion(test=True)


@test
def api():
    from myqueue import submit
    from myqueue.task import task
    submit(task('myqueue.test@oom 1'))
    submit(task('myqueue.test@timeout_once', tmax='1s'))
    submit(task('myqueue.test@timeout_once'))
    wait()
    assert states() == 'MTd'
