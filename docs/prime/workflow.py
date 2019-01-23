from myqueue.task import task

def create_tasks():
    return [task('prime.factor'),
            task('prime.check', deps='prime.factor')]
