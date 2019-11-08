import os
import signal
import socket
import subprocess
import sys
from time import sleep, time
from pathlib import Path
from typing import Tuple

from .utils import get_home_folders

T = 600  # ten minutes

out = Path.home() / '.myqueue/daemon.out'
err = Path.home() / '.myqueue/daemon.err'
pidfile = Path.home() / '.myqueue/daemon.pid'


def alive() -> bool:
    if out.is_file() and pidfile.is_file():
        age = time() - out.stat().st_mtime
        if age < 7200:
            return True
    return False


def start_daemon() -> bool:
    if err.is_file():
        msg = (f'Something wrong.  See {err}.  '
               'Fix the problem and remove the daemon.err file.')
        raise RuntimeError(msg)

    if alive():
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


def exit(signum, frame):
    pidfile.unlink()
    sys.exit()


def read_hostname_and_pid() -> Tuple[str, int]:
    host, pid = pidfile.read_text().split(':')
    return host, int(pid)


def loop() -> None:
    dir = out.parent

    pid = os.getpid()
    host = socket.gethostname()
    pidfile.write_text(f'{host}:{pid}\n')

    signal.signal(signal.SIGWINCH, exit)
    signal.signal(signal.SIGTERM, exit)

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


def perform_action(action: str) -> int:
    running = alive()
    if running:
        host, pid = read_hostname_and_pid()

    if action == 'status':
        if running:
            print(f'Running on {host} with pid={pid}')
        else:
            print('Not running')

    elif action == 'stop':
        if running:
            if host == socket.gethostname():
                os.kill(pid, signal.SIGWINCH)
            else:
                print('You have to be on {host} in order to stop the daemon')
                return 1
        else:
            print('Not running')

    elif action == 'start':
        if running:
            print('Already running')
        else:
            start_daemon()
            while not pidfile.is_file():
                sleep(0.05)
            host, pid = read_hostname_and_pid()
            print(f'PID: {pid}')

    else:
        assert False, action

    return 0
