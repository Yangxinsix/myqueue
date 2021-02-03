from myqueue.workflow import run, resources


@resources(tmax='2s', cores=1)
def workflow():
    with run(module='prime.factor'):
        run(module='prime.check')
