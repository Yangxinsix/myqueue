from myqueue.config import Configuration
from myqueue.schedulers.scheduler import Scheduler


class SchedulerError(Exception):
    """Error from scheduler command."""


def get_scheduler(config: Configuration) -> Scheduler:
    """Create scheduler from config object."""
    name = config.scheduler.lower()
    if name == 'test':
        from myqueue.schedulers.test import TestScheduler
        assert TestScheduler.current_scheduler is not None
        return TestScheduler.current_scheduler
    if name == 'local':
        from myqueue.schedulers.local import LocalScheduler
        return LocalScheduler(config)
    if name == 'slurm':
        from myqueue.schedulers.slurm import SLURM
        return SLURM(config)
    if name == 'pbs':
        from myqueue.schedulers.pbs import PBS
        return PBS(config)
    if name == 'lsf':
        from myqueue.schedulers.lsf import LSF
        return LSF(config)
    raise ValueError(f'Unknown scheduler: {name}')
