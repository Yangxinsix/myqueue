from pathlib import Path
import subprocess

from ..queue import Queue
from ..task import task


def test_completion():
    from myqueue.utils import update_completion
    update_completion(test=True)


def test_api(mq):
    from myqueue import submit
    from myqueue.task import task
    submit(task('myqueue.test@oom 1'))
    submit(task('myqueue.test@timeout_once', tmax='1s'))
    submit(task('myqueue.test@timeout_once'))
    mq.wait()
    assert mq.states() == 'MTd'


def test_logo():
    from myqueue.logo import create
    create()


def test_backends(mq):
    from ..config import config, guess_scheduler, main
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
        config['scheduler'] = 'test'
        del config['nodes']
        del config['mpiexec']
    guess_scheduler()
    main('local')


class Result:
    def __init__(self, stdout):
        self.stdout = stdout


def run(commands, stdout):
    if commands[0] == 'sinfo':
        return Result(b'8 256000+ xeon8*\n')
    return Result(b'id state 8:8 load xeon8 128 G\n')


def test_autoconfig(monkeypatch):
    from ..slurm import SLURM
    from ..lsf import LSF
    monkeypatch.setattr(subprocess, 'run', run)
    nodes = SLURM().get_config()
    assert nodes == [('xeon8', 8, '256000M')]
    nodes = LSF().get_config()
    assert nodes == [('xeon8', 8, '128G')]


def test_commands():
    from ..commands import convert, create_command, ShellScript
    assert convert('True') is True
    assert convert('False') is False
    assert convert('3.14') == 3.14
    assert convert('42') == 42
    cmd = create_command('./script.sh 1 2')
    assert isinstance(cmd, ShellScript)
    assert cmd.todict()['args'] == ['1', '2']
    print(cmd)


def test_resource_comments(tmp_path):
    from ..task import task
    script = tmp_path / 'script.py'
    script.write_text('# Script\n# MQ: resources=2:1h\n')
    t = task(str(script))
    assert t.resources.cores == 2
    assert t.resources.tmax == 3600
