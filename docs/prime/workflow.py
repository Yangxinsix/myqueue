from myqueue.task import task


def create_tasks():
    return [task('prime.factor', creates=['factors.json']),
            task('prime.check', deps='prime.factor')]
