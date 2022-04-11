import subprocess

import pytest
from myqueue.task import task as create_task


class Result:
    def __init__(self, stdout):
        self.stdout = stdout


def run(commands, stdout=None, env=None, capture_output=None, input=None):
    """Fake subprocess.run() function."""
    # slurm:
    if commands[0] == 'sbatch':
        return Result(b'ID: 42\n')
    if commands[0] == 'sacct':
        return Result(b'1K\n')
    if commands[0] == 'squeue':
        return Result(b'bla-bla\n1\n2\n')
    if commands[0] == 'scontrol':
        return
    if commands[0] == 'scancel':
        return

    # pbs:
    if commands[0] == 'qsub':
        return Result(b'42.hmmm\n')
    if commands[0] == 'qdel':
        return
    if commands[0] == 'qstat':
        return Result(b'bla-bla\n1.x abc\n2.x abc\n')

    # lsf:
    if commands[0] == 'bsub':
        return Result(b'bla-bla: j42.\n')
    if commands[0] == 'bsub':
        return
    if commands[0] == 'bkill':
        return
    if commands[0] == 'bjobs':
        return Result(b'bla-bla\n1 x\n2 abc\n')

    assert False, commands


@pytest.mark.parametrize('name', ['slurm', 'pbs', 'lsf'])
def test_scheduler_subprocess(monkeypatch, name):
    from ..config import Configuration
    from ..scheduler import get_scheduler

    monkeypatch.setattr(subprocess, 'run', run)

    config = Configuration(name)
    config.nodes = [('abc16', {'cores': 16, 'memory': '16G'}),
                    ('abc8', {'cores': 8, 'memory': '8G'})]
    scheduler = get_scheduler(config)
    t = create_task('x', resources='2:1h')
    scheduler.submit(t, dry_run=True, verbose=True)
    scheduler.submit(t)
    assert t.id == '42'
    if name == 'slurm':
        scheduler.hold(t)
        scheduler.release_hold(t)
        assert scheduler.maxrss('1') == 1000
    scheduler.cancel(t)
    assert scheduler.get_ids() == {'1', '2'}
