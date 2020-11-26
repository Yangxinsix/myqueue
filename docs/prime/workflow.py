from myqueue.task import task


def create_tasks():
    return [task('prime.factor', creates=['factors.json']),
            task('prime.check', deps='prime.factor')]


def workflow(run):
    f = run('prime.factor', creates=['factors.json']),
    run('prime.check', deps=[f])
