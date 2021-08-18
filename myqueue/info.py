import json
import os
import textwrap
from pathlib import Path
from typing import Generator

from myqueue import __version__
from myqueue.config import Configuration
from myqueue.pretty import pprint
from myqueue.progress import Spinner
from myqueue.queue import Queue
from myqueue.selection import Selection


def info(queue: Queue, id: int = None) -> None:
    """Print information about MyQueue or a single task."""
    if id is None:
        print('Version:', __version__)
        print('Code:   ', Path(__file__).parent)
        print('Root:   ', queue.config.home / '.myqueue')
        print('\nConfiguration:')
        print(textwrap.indent(str(queue.config), '  '))
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
    spinner = Spinner()
    for path in scan(start, dev, spinner):
        spinner.reset()
        print(f'{path}:\n  ', end='')
        try:
            config = Configuration.read(path)
        except FileNotFoundError as ex:
            print(ex)
            continue
        with Queue(config, need_lock=False) as queue:
            queue._read()
            pprint(queue.tasks, short=True)
    spinner.reset()
    print(' ')


def scan(path: Path,
         dev: int,
         spinner: Spinner) -> Generator[Path, None, None]:
    """Scan for .myqueue folders.

    Only yield paths on same filesystem (dev).
    """
    with os.scandir(path) as entries:
        for entry in entries:
            spinner.spin()
            if entry.is_dir(follow_symlinks=False):
                if entry.name == '.myqueue':
                    yield path / entry.name
                elif (not entry.name.startswith(('.', '_')) and
                      entry.stat().st_dev == dev):
                    yield from scan(path / entry.name, dev, spinner)
