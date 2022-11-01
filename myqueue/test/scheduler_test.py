import subprocess

import pytest
from myqueue.schedulers import SchedulerError
from myqueue.task import create_task


class Result:
    def __init__(self, stdout, stderr=b'', returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def run(commands,
        stdout=None,
        env=None,
        capture_output=None,
        input=None):
    """Fake subprocess.run() function."""
    # slurm:
    if any('FAIL' in arg for arg in commands):
        return Result(b'', b'FAIL', 1)
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
    if commands[0] == 'bkill':
        return
    if commands[0] == 'bjobs':
        return Result(b'bla-bla\n1 x\n2 abc\n')

    assert False, commands


@pytest.mark.parametrize('name', ['slurm', 'pbs', 'lsf'])
def test_scheduler_subprocess(monkeypatch, name):
    from myqueue.config import Configuration
    from myqueue.schedulers import get_scheduler

    monkeypatch.setattr(subprocess, 'run', run)

    config = Configuration(name)
    config.nodes = [('abc16', {'cores': 16, 'memory': '16G'}),
                    ('abc8', {'cores': 8, 'memory': '8G'})]
    scheduler = get_scheduler(config)
    t = create_task('x', resources='2:1h')
    scheduler.submit(t, dry_run=True, verbose=True)
    id = scheduler.submit(t)
    assert id == 42
    if name == 'slurm':
        scheduler.hold(42)
        scheduler.release_hold(42)
        assert scheduler.maxrss(1) == 1000
    scheduler.cancel(42)
    assert scheduler.get_ids() == {1, 2}

    t = create_task('FAIL', resources='2:1h')
    with pytest.raises(SchedulerError, match='FAIL'):
        scheduler.submit(t)
