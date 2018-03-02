import errno
import os
import re
import sys
import time
from contextlib import contextmanager
from typing import IO, Union


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
        fd = os.fdopen(fd, 'wb')
        return fd


class Lock:
    def __init__(self, name: str):
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
