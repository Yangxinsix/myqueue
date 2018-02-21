#!/usr/bin/env python3
"""Bash completion.

Put this in your .bashrc::

    alias tasks="python3 -m c2dm.tasks"
    complete -o default -C "python3 -m c2dm.tasks.complete" tasks

"""

import os
import sys
from glob import glob


def match(word, *suffixes):
    return [w for w in glob(word + '*')
            if any(w.endswith(suffix) for suffix in suffixes)]


commands = {
    'list': ['-s', '--states'],
    'submit': ['-o', '--only'],
    'run': ['-0', '--dry-run'],
    'clear': ['-s', '--status']}


def complete(word, previous, line, point):
    for w in line[:point - len(word)].strip().split()[1:]:
        if w[0].isalpha():
            if w in commands:
                command = w
                break
    else:
        opts = ['-h', '--help', '-v', '--verbose', '--flags',
                '-w', '--workflow']
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
