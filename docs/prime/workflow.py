from pathlib import Path
from myqueue import run
from myqueue.task import task


def create_tasks():
    return [task('prime.factor', creates=['factors.json']),
            task('prime.check', deps='prime.factor')]


def workflow():
    with run(module='prime.factor', done=Path('factors.json').is_file()):
        run(module='prime.check')
