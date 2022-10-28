from __future__ import annotations
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.task import Task
from myqueue.pretty import pprint


def ls(queue: Queue,
       selection: Selection,
       columns: str,
       sort: str | None = None,
       reverse: bool = False,
       short: bool = False,
       verbosity: int = 1) -> list[Task]:
    """Pretty-print list of tasks."""
