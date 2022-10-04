from myqueue.config import Configuration
from myqueue.schedulers.scheduler import Scheduler


class SchedulerError(Exception):
    """Error from scheduler command."""


def get_scheduler(config: Configuration) -> Scheduler:
    """Create scheduler from config object."""
    name = config.scheduler.lower()
    if name == 'test':
        from myqueue.test.scheduler import TestScheduler
        assert TestScheduler.current_scheduler is not None
        return TestScheduler.current_scheduler
    if name == 'local':
        from myqueue.local import LocalScheduler
        return LocalScheduler(config)
    if name == 'slurm':
        from myqueue.slurm import SLURM
        return SLURM(config)
    if name == 'pbs':
        from myqueue.pbs import PBS
        return PBS(config)
    if name == 'lsf':
        from myqueue.lsf import LSF
        return LSF(config)
    raise ValueError(f'Unknown scheduler: {name}')
