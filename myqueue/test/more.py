from pathlib import Path
from .runner import test, wait, states
from ..queue import Queue
from ..task import task


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


@test
def logo():
    from myqueue.logo import create
    create()


@test
def backends():
    from ..config import config
    config['nodes'] = [('abc16', {'cores': 16, 'memory': '16G'}),
                       ('abc8', {'cores': 8, 'memory': '8G'})]
    config['mpiexec'] = 'echo'
    try:
        for name in ['slurm', 'lsf', 'pbs']:
            print(name)
            if name == 'pbs':
                p = Path('venv/bin/')
                p.mkdir(parents=True)
                (p / 'activate').write_text('')
            config['scheduler'] = name
            with Queue(dry_run=True, verbosity=2) as q:
                q.submit([task('shell:echo hello', cores=24)])
    finally:
        config['scheduler'] = 'local'
        del config['nodes']
        del config['mpiexec']


@test
def doctests():
    import doctest
    import myqueue.utils as utils
    doctest.testmod(utils)
