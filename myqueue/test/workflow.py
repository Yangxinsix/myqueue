def create_tasks():
    from myqueueue.task import task
    t1 = task('sleep+5')
    t2 = task('echo+j2', deps=[t1])
    tasks = [
        t1,
        t2,
        task('echo+j3', deps=[t1]),
        task('echo+j4', deps=[t2])]
    return tasks
