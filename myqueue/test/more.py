from .testrunner import test


@test
def completion():
    from myqueue.utils import update_completion
    update_completion(test=True)
