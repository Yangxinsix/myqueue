from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .task import Task  # noqa


__version__ = '19.2.1b1'


def submit(*tasks: List['Task'], verbosity: int = 1, dry_run: bool = False):
    """Submit tasks.

    Parameters
    ----------

    tasks: List of Task objects
        Tasks to submit.
    verbosity: int
        Must be 0, 1 or 2.
    dry_run: bool
        Don't actually submit the task.
    """
    from .runner import Runner
    with Runner(verbosity) as runner:
        runner.submit(tasks, dry_run)
