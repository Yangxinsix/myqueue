from myqueue.task import task


def create_tasks():
    return [task('task1'),
            task('task2', deps='task1')]
