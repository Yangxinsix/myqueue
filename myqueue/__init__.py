from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .task import Task  # noqa


__version__ = '19.2.1b1'


def submit(*tasks: List['Task'], verbosity: int = 1, dry_run: bool = False):
    from .runner import Runner
    with Runner(verbosity) as runner:
        runner.submit(tasks, dry_run)
