import json
import os
import textwrap
from pathlib import Path

from myqueue import __version__
from myqueue.queue import Queue
from myqueue.selection import Selection
from myqueue.config import Configuration
from myqueue.pretty import pprint


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


class Spinner:
    n = 0

    def spin(self):
        N = 500
        if self.n % N == 0:
            print('\r' + '.oOo. '[(self.n // N) % 6], end='')
        self.n += 1


def info_all(start: Path):
    dev = start.stat().st_dev
    '.oOo. '
    for path in scan(start, dev, Spinner()):
        print(f'\r{path}:')
        try:
            config = Configuration.read(path)
        except FileNotFoundError:
            continue
        with Queue(config, need_lock=False) as queue:
            queue._read()
            pprint(queue.tasks, short=True)


def scan(path, dev, spinner):
    with os.scandir(path) as entries:
        for entry in entries:
            spinner.spin()
            if entry.is_dir(follow_symlinks=False):
                if entry.name == '.myqueue':
                    yield path / entry.name
                elif (not entry.name.startswith(('.', '_')) and
                      entry.stat().st_dev == dev):
                    yield from scan(path / entry.name, dev, spinner)
