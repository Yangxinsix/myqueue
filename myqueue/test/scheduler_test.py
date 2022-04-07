import subprocess
from myqueue.task import task as create_task


class Result:
    def __init__(self, stdout):
        self.stdout = stdout


def run(commands, stdout=None, env=None, capture_output=None, input=None):
    if commands[0] == 'sbatch':
        return Result(b'ID: 42\n')
    if commands[0] == 'sacct':
        return Result(b'1K\n')
    if commands[0] == 'squeue':
        return Result(b'bla-bla\n1\n2\n')


def test_slurm(monkeypatch):
    from ..scheduler import get_scheduler
    from ..config import Configuration

    monkeypatch.setattr(subprocess, 'run', run)

    config = Configuration('slurm')
    config.nodes = [('abc16', {'cores': 16, 'memory': '16G'}),
                    ('abc8', {'cores': 8, 'memory': '8G'})]
    scheduler = get_scheduler(config)
    t = create_task('x', resources='2:1h')
    scheduler.submit(t, dry_run=True, verbose=True)
    scheduler.submit(t)
    assert t.id == '42'
    scheduler.hold(t)
    scheduler.release_hold(t)
    scheduler.cancel(t)
    assert scheduler.get_ids() == {'1', '2'}
    assert scheduler.maxrss('1') == 1000
