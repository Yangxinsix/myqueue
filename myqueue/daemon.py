import functools
import os
import signal
import socket
import sys
import traceback
from pathlib import Path
from time import sleep, time
from typing import Any, Tuple

from myqueu.queue import Queue
from myqueue.config import Configuration

T = 600  # Kick system every ten minutes


def is_running(mq: Path) -> bool:
    out = mq / 'daemon.out'
    if out.is_file() and (mq / 'daemon.pid').is_file():
        age = time() - out.stat().st_mtime
        if age < 7200:
            return True
    return False


def start_daemon(mq: Path) -> bool:
    err = mq / 'daemon.err'
    out = mq / 'daemon.out'

    if err.is_file():
        msg = (f'Something wrong.  See {err}.  '
               'Fix the problem and remove the daemon.err file.')
        raise RuntimeError(msg)

    if is_running():
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
            loop(mq)
        os._exit(0)
    return True


def exit(pidfile: Path, signum: int, frame: Any) -> None:
    pidfile.unlink()
    sys.exit()


def read_hostname_and_pid(pidfile: Path) -> Tuple[str, int]:
    host, pid = pidfile.read_text().split(':')
    return host, int(pid)


def loop(mq: Path) -> None:
    err = mq / 'daemon.err'
    out = mq / 'daemon.out'
    pidfile = mq / 'daemon.pid'

    pid = os.getpid()
    host = socket.gethostname()
    pidfile.write_text(f'{host}:{pid}\n')

    cleanup = functools.partial(exit, pidfile)
    signal.signal(signal.SIGWINCH, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    config = Configuration.read(mq)

    while True:
        sleep(T)
        if mq.is_dir():
            try:
                with Queue(config, verbosity=0) as queue:
                    restarted, held, released = queue.kick()
            except Exception:
                err.write_text(traceback.format_exc())
                return
        else:
            return

        if restarted + held + released > 0:
            with out.open('a') as fd:
                print(restarted, held, released, file=fd)
        else:
            out.touch()


def perform_action(mq: Path, action: str) -> int:
    pidfile = mq / 'daemon.pid'

    running = is_running(mq)
    if running:
        host, pid = read_hostname_and_pid(pidfile)

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
                print(f'You have to be on {host} in order to stop the daemon')
                return 1
        else:
            print('Not running')

    elif action == 'start':
        if running:
            print('Already running')
        else:
            assert not pidfile.is_file()
            start_daemon(mq)
            while not pidfile.is_file():
                # Wait for the fork to start ...
                sleep(0.05)
            host, pid = read_hostname_and_pid(pidfile)
            print(f'PID: {pid}')

    else:
        assert False, action

    return 0
