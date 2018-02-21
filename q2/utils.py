import errno
import os
import time
from contextlib import contextmanager


@contextmanager
def chdir(folder):
    dir = os.getcwd()
    os.chdir(str(folder))
    yield
    os.chdir(dir)


def opencew(filename):
    """Create and open filename exclusively for writing.

    If master cpu gets exclusive write access to filename, a file
    descriptor is returned (a dummy file descriptor is returned on the
    slaves).  If the master cpu does not get write access, None is
    returned on all processors."""

    try:
        fd = os.open(filename, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except OSError as ex:
        if ex.errno == errno.EEXIST:
            return None
        raise
    else:
        fd = os.fdopen(fd, 'wb')
        return fd


class Lock:
    def __init__(self, name='lock', world=None):
        self.name = str(name)

        if world is None:
            from ase.parallel import world
        self.world = world

    def acquire(self):
        while True:
            fd = opencew(self.name, self.world)
            if fd is not None:
                break
            time.sleep(1.0)

    def release(self):
        self.world.barrier()
        if self.world.rank == 0:
            os.remove(self.name)

    def __enter__(self):
        self.acquire()

    def __exit__(self, type, value, tb):
        self.release()
