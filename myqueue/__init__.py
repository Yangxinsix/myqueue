"""Top level module definitions.

The version number and the submit() function is defined here.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from myqueue.task import Task


__version__ = '22.12.0'


def submit(*tasks: Task, verbosity: int = 1, dry_run: bool = False) -> None:
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
    from myqueue.queue import Queue
    from myqueue.config import Configuration
    from myqueue.submitting import submit as _submit

    config = Configuration.read()
    with Queue(config, dry_run=dry_run) as queue:
        _submit(queue, tasks, verbosity=verbosity)
