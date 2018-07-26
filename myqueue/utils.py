import errno
import os
import re
import sys
import time
from contextlib import contextmanager
from io import StringIO
from typing import IO, Union, Generator
from pathlib import Path


@contextmanager
def chdir(folder: Path) -> Generator:
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
        self.lock = name

    def acquire(self):
        delta = 0.1
        while True:
            fd = opencew(str(self.lock))
            if fd is not None:
                break
            time.sleep(delta)
            delta *= 2

    def release(self):
        self.lock.unlink()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, type, value, tb):
        self.release()


def lock(method):
    def m(self, *args, **kwargs):
        with self:
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
    """Update README.rst and commands dict.

    Run this when ever options are changed::

        python3 -m myqueue.utils

    """

    import argparse
    import textwrap
    from myqueue.cli import main

    # Path of the complete.py script:
    dir = Path(__file__).parent

    sys.stdout = StringIO()
    for cmd in ['list', 'submit', 'resubmit', 'remove', 'workflow',
                'sync', 'completion', 'test']:
        print('\n\n{} command\n{}\n'
              .format(cmd.title(), '-' * (len(cmd) + 8)))
        main(['help', cmd])

    newlines = sys.stdout.getvalue().splitlines()
    sys.stdout = sys.__stdout__

    n = 0
    while n < len(newlines):
        line = newlines[n]
        if line == 'positional arguments:':
            L = []
            n += 1
            while True:
                line = newlines.pop(n)
                if not line:
                    break
                if not line.startswith('                '):
                    cmd, help = line.strip().split(' ', 1)
                    L.append('{}:\n    {}'.format(cmd, help.strip()))
                else:
                    L[-1] += ' ' + line.strip()
            newlines[n - 1:n] = L + ['']
            n += len(L)
        n += 1

    readme = dir / '../README.rst'

    lines = readme.read_text().splitlines()
    a = lines.index('.. computer generated text:')
    lines[a + 4:] = newlines
    readme.write_text('\n'.join(lines))

    filename = dir / 'complete.py'

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
    txt = txt[:-1] + '}'

    lines = filename.read_text().splitlines()

    a = lines.index('# Beginning of computer generated data:')
    b = lines.index('# End of computer generated data')
    lines[a + 1:b] = [txt]

    filename.write_text('\n'.join(lines) + '\n')


if __name__ == '__main__':
    update_completion()
