from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Generator, Callable
from math import inf
import rich.progress as progress
from rich.table import Table
from rich.console import Console

from myqueue import __version__
from myqueue.config import Configuration
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.virtenv import find_activation_scripts


def info(queue: Queue, id: str = None) -> None:
    """Print information about MyQueue or a single task."""

    cwd = Path.cwd()
    venv = find_activation_scripts([cwd]).get(cwd, '<none>')
    print = Console().print

    if id is None:
        table = Table(title=f'MyQueue-{__version__}')
        table.add_column(style='green')
        table.add_column('Path', style='cyan')
        table.add_row('Code', str(Path(__file__).parent))
        table.add_row('Root', str(queue.config.home / '.myqueue'))
        table.add_row('Venv', str(venv))
        print(table)

        table = Table(title='Configuration')
        table.add_column('Key', style='green')
        table.add_column('Value', style='yellow')
        for key, value in queue.config.__dict__.items():
            if key == 'nodes':
                continue
            table.add_row(key, str(value))
        print(table)

        table = Table(title='Nodes')
        table.add_column('Name', style='green')
        table.add_column('Values', style='yellow')
        for name, dct in queue.config.nodes:
            table.add_row(name, str(dct))
        print(table)

        return

    queue._read()
    task = Selection({id}).select(queue.tasks)[0]
    print(json.dumps(task.todict(), indent='    '))
    if queue.verbosity > 1:
        path = queue.scheduler.error_file(task)
        try:
            err = path.read_text()
        except FileNotFoundError:
            pass
        else:
            try:
                N = os.get_terminal_size().columns - 1
            except OSError:
                N = 70
            print(f'\nError file: {path}')
            print('v' * N)
            print(err)
            print('^' * N)


def info_all(start: Path) -> None:
    """Write information about all .myqueue folders."""
    dev = start.stat().st_dev
    nfolders = 0
    spinner = progress.Progress('[progress.description]{task.description}',
                                progress.SpinnerColumn('pong'),
                                transient=True)
    p = spinner.console.print

    with spinner:
        id = spinner.add_task('Searching', total=inf)
        for path in scan(start, dev, lambda: spinner.advance(id)):
            p(f'{path}:\n  ', end='')
            try:
                config = Configuration.read(path)
                nfolders += 1
            except FileNotFoundError as ex:
                p(f'[red]{ex}')
                continue
            with Queue(config, need_lock=False) as queue:
                queue._read()
                from collections import defaultdict
                count: dict[str, int] = defaultdict(int)
                for task in queue.tasks:
                    count[task.state.name] += 1
                count['total'] = len(queue.tasks)
                states = []
                for state, n in count.items():
                    if state == 'done':
                        state = '[green]done[/]'
                    elif state == 'running':
                        state = '[yellow]running[/]'
                    elif state.isupper():
                        state = f'[red]{state}[/]'
                    states.append(f'{state}: {n}')
                p(', '.join(states))
    print('Folders found:', nfolders)


def scan(path: Path,
         dev: int,
         spin: Callable[[], None]) -> Generator[Path, None, None]:
    """Scan for .myqueue folders.

    Only yield paths on same filesystem (dev).
    """

    with os.scandir(path) as entries:
        for entry in entries:
            spin()
            if entry.is_dir(follow_symlinks=False):
                if entry.name == '.myqueue':
                    yield path / entry.name
                elif (not entry.name.startswith(('.', '_')) and
                      entry.stat().st_dev == dev):
                    yield from scan(path / entry.name, dev, spin)
