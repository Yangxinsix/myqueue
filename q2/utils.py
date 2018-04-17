import errno
import os
import re
import sys
import time
from contextlib import contextmanager
from typing import IO, Union
from pathlib import Path


@contextmanager
def chdir(folder):
    dir = os.getcwd()
    os.chdir(str(folder))
    yield
    os.chdir(dir)


def opencew(filename: str) -> Union[IO[bytes], None]:
    """Create and open filename exclusively for writing.

    If master cpu gets exclusive write access to filename, a file
    descriptor is returned (a dummy file descriptor is returned on the
    slaves).  If the master cpu does not get write access, None is
    returned on all processors."""

    try:
        fd = os.open(str(filename), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            return None
        raise
    else:
        return os.fdopen(fd, 'wb')


class Lock:
    def __init__(self, name: Path) -> None:
        self.name = str(name)

    def acquire(self):
        while True:
            fd = opencew(self.name)
            if fd is not None:
                break
            time.sleep(1.0)

    def release(self):
        os.remove(self.name)

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, type, value, tb):
        self.release()


def lock(method):
    def m(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)
    return m


regex = re.compile(r'\{.*?\}')


class F:
    def __pow__(self, arg):
        context = sys._getframe(1).f_locals
        parts = []
        for match in regex.finditer(arg):
            a, b = match.span()
            x = arg[a + 1:b - 1]
            if x[0] == '{':
                continue
            if ':' in x:
                x, fmt = x.split(':')
            else:
                fmt = ''
            s = format(eval(x, context), fmt)
            parts.append((a, b, s))
        for a, b, s in reversed(parts):
            arg = arg[:a] + s + arg[b:]
        return arg


f = F()


def update_completion():
    """Update commands dict.

    Run this when ever options are changed::

        python3 -m q2.utils

    """

    import argparse
    import collections
    import textwrap
    from q2.cli import main

    # Path of the complete.py script:
    my_dir, _ = os.path.split(os.path.realpath(__file__))
    filename = os.path.join(my_dir, 'complete.py')

    dct = {}

    class MyException(Exception):
        pass

    class Parser:
        def __init__(self, **kwargs):
            pass

        def add_argument(self, *args, **kwargs):
            pass

        def add_subparsers(self, **kwargs):
            return self

        def add_parser(self, cmd, **kwargs):
            return Subparser(cmd)

        def parse_args(self, args=None):
            raise MyException

    class Subparser:
        def __init__(self, command):
            self.command = command
            dct[command] = []

        def add_argument(self, *args, **kwargs):
            dct[self.command].extend(arg for arg in args
                                     if arg.startswith('-'))

    argparse.ArgumentParser = Parser
    try:
        main()
    except MyException:
        pass

    txt = 'commands = {'
    for command, opts in sorted(dct.items()):
        txt += "\n    '" + command + "':\n        ["
        txt += '\n'.join(textwrap.wrap("'" + "', '".join(opts) + "'],",
                         width=65,
                         break_on_hyphens=False,
                         subsequent_indent='         '))
    txt = txt[:-1] + '}\n'
    with open(filename) as fd:
        lines = fd.readlines()
        a = lines.index('# Beginning of computer generated data:\n')
        b = lines.index('# End of computer generated data\n')
    lines[a + 1:b] = [txt]
    with open(filename + '.new', 'w') as fd:
        print(''.join(lines), end='', file=fd)
    os.rename(filename + '.new', filename)


if __name__ == '__main__':
    update_completion()
