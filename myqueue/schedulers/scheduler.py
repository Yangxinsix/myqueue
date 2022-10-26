from __future__ import annotations

import os
from pathlib import Path

from myqueue.config import Configuration
from myqueue.task import Task


class Scheduler:
    def __init__(self, config: Configuration):
        self.config = config
        self.name = config.scheduler.lower()
        venv = os.environ.get('VIRTUAL_ENV')
        self.activation_script = (Path(venv) / 'bin/activate'
                                  if venv is not None else None)

    def get_venv_activation_line(self) -> str:
        if self.activation_script:
            return (f'source {self.activation_script}\n'
                    f'echo "venv: {self.activation_script}"\n')
        return ''

    def submit(self,
               task: Task,
               dry_run: bool = False,
               verbose: bool = False) -> int:
        """Submit a task."""
        raise NotImplementedError

    def cancel(self, id: int) -> None:
        """Cancel a task."""
        raise NotImplementedError

    def get_ids(self) -> set[int]:
        """Get ids for all tasks the scheduler knows about."""
        raise NotImplementedError

    def hold(self, id: int) -> None:
        raise NotImplementedError

    def release_hold(self, id: int) -> None:
        raise NotImplementedError

    def error_file(self, task: Task) -> Path:
        return task.folder / f'{task.cmd.short_name}.{task.id}.err'

    def has_timed_out(self, task: Task) -> bool:
        path = self.error_file(task).expanduser()
        if path.is_file():
            task.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines:
                if line.endswith('DUE TO TIME LIMIT ***'):
                    return True
        return False

    def maxrss(self, id: int) -> int:
        return 0

    def get_config(self, queue: str = '') -> tuple[list[tuple[str, int, str]],
                                                   list[str]]:
        raise NotImplementedError
