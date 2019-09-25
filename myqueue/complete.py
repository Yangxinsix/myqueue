#!/usr/bin/env python3
"""Bash completion.

Put this in your .bashrc::

    complete -o default -C "python3 -m myqueue.complete" mq

"""

import os
import sys
from glob import glob
from typing import List, Dict, Any, Iterable


def match(word: str, *suffixes: str) -> List[str]:
    return [w for w in glob(word + '*')
            if any(w.endswith(suffix) for suffix in suffixes)]


def read() -> Dict[str, Any]:
    from pathlib import Path
    import json
    path = Path.home() / '.myqueue/queue.json'
    try:
        dct: Dict[str, Any] = json.loads(path.read_text())
        return dct
    except Exception:
        return {}


# Beginning of computer generated data:
commands = {
    'completion':
        ['-v', '--verbose', '-q', '--quiet', '-T', '--traceback'],
    'help':
        [''],
    'info':
        ['-v', '--verbose', '-q', '--quiet', '-T', '--traceback'],
    'init':
        ['-z', '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback'],
    'kick':
        ['-z', '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback', '-A', '--all'],
    'list':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-c',
         '--columns', '-S', '--sort', '-C', '--count', '-v',
         '--verbose', '-q', '--quiet', '-T', '--traceback', '-A',
         '--all'],
    'modify':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-z',
         '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback', '-r', '--recursive'],
    'remove':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-z',
         '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback', '-r', '--recursive'],
    'resubmit':
        ['-R', '--resources', '-w', '--workflow', '-s', '--states', '-i',
         '--id', '-n', '--name', '-z', '--dry-run', '-v',
         '--verbose', '-q', '--quiet', '-T', '--traceback', '-r',
         '--recursive'],
    'run':
        ['-n', '--name', '-w', '--workflow', '-z', '--dry-run', '-v',
         '--verbose', '-q', '--quiet', '-T', '--traceback'],
    'submit':
        ['-d', '--dependencies', '-n', '--name', '--restart', '-f',
         '--force', '-R', '--resources', '-w', '--workflow',
         '-z', '--dry-run', '-v', '--verbose', '-q', '--quiet',
         '-T', '--traceback'],
    'sync':
        ['-z', '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback', '-A', '--all'],
    'test':
        ['--config-file', '-x', '--exclude', '-u', '--update-source-code',
         '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback'],
    'workflow':
        ['-f', '--force', '-t', '--targets', '-p', '--pattern', '-z',
         '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback']}
# End of computer generated data


def complete(word: str, previous: str, line: str, point: int) -> Iterable[str]:
    for w in line[:point - len(word)].strip().split()[1:]:
        if w[0].isalpha():
            if w in commands:
                command = w
                break
    else:
        opts = ['-h', '--help', '-V', '--version']
        if word[:1] == '-':
            return opts
        return list(commands.keys()) + opts

    if word[:1] == '-':
        return commands[command]

    if previous in ['-n', '--name']:
        dct = read()
        words = set()
        for task in dct['tasks']:
            cmd = task['cmd']
            words.add((cmd['cmd'] + '+' + '_'.join(cmd['args'])).rstrip('+'))
        return words

    if previous in ['-i', '--id']:
        dct = read()
        return {str(task['id']) for task in dct['tasks']}

    if command == 'test':
        from myqueue.test.runner import all_tests, find_tests
        find_tests()
        return all_tests.keys()

    if command == 'help':
        return [cmd for cmd in commands if cmd != 'help']

    return []


word, previous = sys.argv[2:]
line = os.environ['COMP_LINE']
point = int(os.environ['COMP_POINT'])
words = complete(word, previous, line, point)
for w in words:
    if w.startswith(word):
        print(w)
