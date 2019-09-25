import os
import subprocess
import sys
from time import sleep, time
from pathlib import Path

from myqueue.utils import get_home_folders

T = 600  # ten minutes

out = Path.home() / '.myqueue/daemon.out'
err = Path.home() / '.myqueue/daemon.err'


def start_daemon() -> bool:
    if err.is_file():
        msg = (f'Something wrong.  See {err}.  '
               'Fix the problem and remove the daemon.err file.')
        raise RuntimeError(msg)

    if out.is_file():
        age = time() - out.stat().st_mtime
        if age < 7200:
            return False

    out.touch()

    pid = os.fork()
    if pid == 0:
        pid = os.fork()
        if pid == 0:
            # redirect standard file descriptors
            sys.stderr.flush()
            si = open(os.devnull, 'r')
            so = open(os.devnull, 'w')
            se = open(os.devnull, 'w')
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())
            loop()
        os._exit(0)
    return True


def loop() -> None:
    dir = out.parent

    while True:
        sleep(T)
        folders = get_home_folders(prune=False)
        newfolders = []
        for f in folders:
            if (f / '.myqueue').is_dir():
                result = subprocess.run(
                    f'python3 -m myqueue kick {f} -T >> {out}',
                    shell=True,
                    stderr=subprocess.PIPE)
                if result.returncode:
                    err.write_bytes(result.stderr)
                    return
                newfolders.append(f)

        out.touch()

        if len(newfolders) < len(folders):
            (dir / 'folders.txt').write_text(
                ''.join(f'{f}\n' for f in newfolders))


if __name__ == '__main__':
    print(start_daemon())
