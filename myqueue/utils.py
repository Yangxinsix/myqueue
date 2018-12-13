import errno
import os
import sys
import time
from contextlib import contextmanager
from io import StringIO
from typing import IO, Union, Generator, List, Dict
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
        self.locked = False

    def acquire(self):
        delta = 0.1
        while True:
            fd = opencew(str(self.lock))
            if fd is not None:
                break
            time.sleep(delta)
            delta *= 2
        self.locked = True

    def release(self):
        if self.locked:
            self.lock.unlink()
            self.locked = False

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


def is_inside(path1: Path, path2: Path) -> bool:
    try:
        path1.relative_to(path2)
    except ValueError:
        return False
    return True


def get_home_folders() -> List[Path]:
    path = Path.home() / '.myqueue' / 'folders.txt'
    if path.is_file():
        folders = []
        for f in path.read_text().splitlines():
            folder = Path(f)
            if (folder / '.myqueue').is_dir():
                folders.append(folder)
        return folders
    else:
        return [Path.home()]


def update_completion() -> None:
    """Update README.rst and commands dict.

    Run this when ever options are changed::

        python3 -m myqueue.utils

    """

    import argparse
    import textwrap
    from myqueue.cli import main, commands, aliases

    aliases = {command: alias for alias, command in aliases.items()}

    # Path of the complete.py script:
    dir = Path(__file__).parent

    sys.stdout = StringIO()

    print('\n.. list-table::')
    print('    :widths: 1 3\n')
    for cmd, (help, description) in commands.items():
        print(f'    * - :ref:`{cmd} <{cmd}>`', end='')
        if cmd in aliases:
            print(f' ({aliases[cmd]})')
        else:
            print()
        print('      -', help.rstrip('.'))

    for cmd, (help, description) in commands.items():
        help = commands[cmd][0].rstrip('.')
        title = f'{cmd.title()}: {help}'
        if cmd in aliases:
            title = title.replace(':', f' ({aliases[cmd]}):')
        print(f'\n\n.. _{cmd}:\n')
        print('{}\n{}\n'.format(title, '-' * len(title)))
        main(['help', cmd])

    txt = sys.stdout.getvalue()
    txt = txt.replace(':\n\n    ', '::\n\n    ')
    newlines = txt.splitlines()
    sys.stdout = sys.__stdout__

    n = 0
    while n < len(newlines):
        line = newlines[n]
        if line == 'positional arguments:':
            L: List[str] = []
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

    readme = dir / '..' / 'docs' / 'cli.rst'

    lines = readme.read_text().splitlines()
    a = lines.index('.. computer generated text:')
    lines[a + 1:] = newlines
    readme.write_text('\n'.join(lines) + '\n')

    filename = dir / 'complete.py'

    dct: Dict[str, List[str]] = {}

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

    argparse.ArgumentParser = Parser  # type: ignore
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
