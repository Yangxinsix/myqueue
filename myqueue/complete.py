#!/usr/bin/env python3
"""Bash completion.

Put this in your .bashrc::

    complete -o default -C "python3 -m myqueue.complete" mq

"""

from __future__ import annotations
import os
import sys
from typing import Iterable, Mapping, TYPE_CHECKING
if TYPE_CHECKING:
    from myqueue.task import Task


def read() -> list[Task]:
    """Read queue as a dict."""
    from pathlib import Path
    from myqueue.config import Configuration
    from myqueue.queue import Queue
    from myqueue.selection import Selection

    config = Configuration.read()
    with Queue(config, need_lock=False) as queue:
        return queue.select(Selection(folders=[Path('.').resolve()]))


# Beginning of computer generated data:
commands = {
    'completion':
        ['-v', '--verbose', '-q', '--quiet', '-T', '--traceback'],
    'config':
        ['-Q', '--queue-name', '--in-place', '-z', '--dry-run', '-v',
         '--verbose', '-q', '--quiet', '-T', '--traceback'],
    'daemon':
        ['-z', '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback'],
    'help':
        [''],
    'info':
        ['-v', '--verbose', '-q', '--quiet', '-T', '--traceback', '-i',
         '--id', '-A', '--all'],
    'init':
        ['-z', '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback'],
    'kick':
        ['-z', '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback'],
    'list':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-e', '--error',
         '-c', '--columns', '-S', '--sort', '-C', '--count',
         '--not-recursive', '-v', '--verbose', '-q', '--quiet',
         '-T', '--traceback'],
    'modify':
        ['-E', '--email', '-N', '--new-state', '-s', '--states', '-i',
         '--id', '-n', '--name', '-e', '--error', '-z',
         '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback', '-r', '--recursive'],
    'remove':
        ['-f', '--force', '-s', '--states', '-i', '--id', '-n', '--name',
         '-e', '--error', '-z', '--dry-run', '-v', '--verbose',
         '-q', '--quiet', '-T', '--traceback', '-r',
         '--recursive'],
    'resubmit':
        ['--remove', '-R', '--resources', '-w', '--workflow', '-X',
         '--extra-scheduler-args', '-s', '--states', '-i',
         '--id', '-n', '--name', '-e', '--error', '-z',
         '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback', '-r', '--recursive'],
    'submit':
        ['-d', '--dependencies', '-n', '--name', '--restart',
         '--max-tasks', '-R', '--resources', '-w', '--workflow',
         '-X', '--extra-scheduler-args', '-z', '--dry-run', '-v',
         '--verbose', '-q', '--quiet', '-T', '--traceback'],
    'sync':
        ['-z', '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback'],
    'workflow':
        ['--max-tasks', '-f', '--force', '-t', '--targets', '-p',
         '--pattern', '-a', '--arguments', '-z', '--dry-run',
         '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback']}
# End of computer generated data

aliases = {'rm': 'remove',
           'ls': 'list'}


def complete(word: str, previous: str, line: str, point: int) -> Iterable[str]:
    for w in line[:point - len(word)].strip().split()[1:]:
        if w[0].isalpha():
            if w in commands or w in aliases:
                command = aliases.get(w, w)
                break
    else:
        opts = ['-h', '--help', '-V', '--version']
        if word[:1] == '-':
            return opts
        return list(commands) + list(aliases) + opts

    if word[:1] == '-':
        return commands[command]

    if previous in ['-n', '--name']:
        tasks = read()
        words = [task.cmd.name for task in tasks]
        return words

    if previous in ['-i', '--id']:
        tasks = read()
        return {str(task.id) for task in tasks}

    if command == 'help':
        return [cmd for cmd in (list(commands) + list(aliases))
                if cmd != 'help']

    if command == 'daemon':
        return ['start', 'stop', 'status']

    return []


def main(environ: Mapping[str, str], word: str, previous: str) -> None:
    line = environ['COMP_LINE']
    point = int(environ['COMP_POINT'])
    words = complete(word, previous, line, point)
    for w in words:
        if w.startswith(word):
            print(w)


if __name__ == '__main__':
    word, previous = sys.argv[2:]
    main(os.environ, word, previous)  # pragma: no cover
