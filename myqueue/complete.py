#!/usr/bin/env python3
"""Bash completion.

Put this in your .bashrc::

    complete -o default -C "python3 -m myqueue.complete" mq

"""

import os
import sys
from glob import glob


def match(word, *suffixes):
    return [w for w in glob(word + '*')
            if any(w.endswith(suffix) for suffix in suffixes)]


def read():
    from pathlib import Path
    import json
    try:
        folder = Path.home() / '.myqueue'
        path = folder / 'runner'
        runner = path.read_text()
        fname = folder / (runner + '.json')
        dct = json.loads(fname.read_text())
        return dct
    except Exception:
        return {}


# Beginning of computer generated data:
commands = {
    'completion':
        ['-v', '--verbose', '-q', '--quiet', '-T', '--traceback'],
    'delete':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-z',
         '--dry-run', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback', '-r', '--recursive'],
    'help':
        [''],
    'list':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-c',
         '--columns', '-v', '--verbose', '-q', '--quiet', '-T',
         '--traceback'],
    'resubmit':
        ['-R', '--resources', '-w', '--workflow', '-s', '--states', '-i',
         '--id', '-n', '--name', '-z', '--dry-run', '-v',
         '--verbose', '-q', '--quiet', '-T', '--traceback', '-r',
         '--recursive'],
    'submit':
        ['-d', '--dependencies', '-a', '--arguments', '-R', '--resources',
         '-w', '--workflow', '-z', '--dry-run', '-v',
         '--verbose', '-q', '--quiet', '-T', '--traceback'],
    'test':
        ['--slurm', '-z', '--dry-run', '-v', '--verbose', '-q', '--quiet',
         '-T', '--traceback'],
    'workflow':
        ['-p', '--pattern', '-z', '--dry-run', '-v', '--verbose', '-q',
         '--quiet', '-T', '--traceback']}
# End of computer generated data


def complete(word, previous, line, point):
    for w in line[:point - len(word)].strip().split()[1:]:
        if w[0].isalpha():
            if w in commands:
                command = w
                break
    else:
        opts = ['-h', '--help']
        if word[:1] == '-':
            return opts
        return list(commands.keys()) + opts

    if word[:1] == '-':
        return commands[command]

    words = []

    if previous in ['-n', '--name']:
        dct = read()
        words = set()
        for job in dct['jobs']:
            cmd = job['cmd']
            words.add((cmd['cmd'] + '+' + '_'.join(cmd['args'])).rstrip('+'))

    elif previous in ['-i', '--id']:
        dct = read()
        words = {str(job['id']) for job in dct['jobs']}

    elif command == 'test':
        from myqueue.test.tests import all_tests as words

    return words


word, previous = sys.argv[2:]
line = os.environ['COMP_LINE']
point = int(os.environ['COMP_POINT'])
words = complete(word, previous, line, point)
for w in words:
    if w.startswith(word):
        print(w)
