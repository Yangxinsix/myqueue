#!/usr/bin/env python3
"""Bash completion.

Put this in your .bashrc::

    complete -o default -C "python3 -m q2.complete" q2

"""

import os
import sys
from glob import glob


def match(word, *suffixes):
    return [w for w in glob(word + '*')
            if any(w.endswith(suffix) for suffix in suffixes)]


# Beginning of computer generated data:
commands = {
    'agts':
        ['-z', '--dry-run', '-r', '--runner'],
    'delete':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-z',
         '--dry-run', '-r', '--runner'],
    'list':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-r',
         '--runner'],
    'resubmit':
        ['-s', '--states', '-i', '--id', '-n', '--name', '-z',
         '--dry-run', '-r', '--runner'],
    'submit':
        ['-R', '--resources', '-d', '--dependencies', '-a', '--arguments',
         '-z', '--dry-run', '-r', '--runner'],
    'workflow':
        ['-z', '--dry-run', '-r', '--runner']}
# End of computer generated data


def complete(word, previous, line, point):
    for w in line[:point - len(word)].strip().split()[1:]:
        if w[0].isalpha():
            if w in commands:
                command = w
                break
    else:
        opts = ['-h', '--help', '-v', '--verbose', '-q', '--quiet']
        if word[:1] == '-':
            return opts
        return list(commands.keys()) + opts

    if word[:1] == '-':
        return commands[command]

    words = []

    if command == 'clear':
        if previous in ['-s', '--status']:
            words = ['todo', 'queued', 'running', 'done', 'FAILED', 'TIMEOUT']

    return words


word, previous = sys.argv[2:]
line = os.environ['COMP_LINE']
point = int(os.environ['COMP_POINT'])
words = complete(word, previous, line, point)
for w in words:
    if w.startswith(word):
        print(w)
