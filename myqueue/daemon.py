"""Background daemon process.

The daemon process wakes up every ten minutes to check if any tasks need to
be resubmitted, held or released.  Notification emails will also be sent.
It will write its output to .myqueue/daemon.out.
"""

from __future__ import annotations
import functools
import os
import signal
import socket
import sys
import traceback
from pathlib import Path
from time import sleep, time
from typing import Any

from myqueue.queue import Queue
from myqueue.config import Configuration
from myqueue.kick import kick

T = 600  # kick system every ten minutes


def is_running(pidfile: Path) -> bool:
    """Check if daemon is running."""
    if pidfile.is_file():
        age = time() - pidfile.stat().st_mtime
        if age < 7200:
            # No action for two hours - it must be dead:
            return True
    return False


def start_daemon(config: Configuration) -> bool:
    """Fork a daemon process."""
    pidfile = config.home / f'.myqueue/daemon-{config.user}.pid'

    if is_running(pidfile):
        return False

    pid = os.fork()
    if pid == 0:
        if os.getenv('MYQUEUE_TESTING'):
            # Simple version for pytest only:
            loop(config)
        else:
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
                loop(config)
        os._exit(0)
    return True


def exit(pidfile: Path, signum: int, frame: Any) -> None:
    """Remove .myqueue/daemon.pid file on exit."""
    if pidfile.is_file():
        pidfile.unlink()
    if not os.getenv('MYQUEUE_TESTING'):
        sys.exit()


def read_hostname_and_pid(pidfile: Path) -> tuple[str, int]:
    """Read from .myqueue/daemon.pid file."""
    host, pid = pidfile.read_text().split(':')
    return host, int(pid)


def loop(config: Configuration) -> None:
    """Main loop: kick system every ten minutes."""
    err = config.home / f'.myqueue/daemon-{config.user}.err'
    out = config.home / f'.myqueue/daemon-{config.user}.out'
    pidfile = config.home / f'.myqueue/daemon-{config.user}.pid'

    pid = os.getpid()
    host = socket.gethostname()
    pidfile.write_text(f'{host}:{pid}\n')

    cleanup = functools.partial(exit, pidfile)
    signal.signal(signal.SIGWINCH, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        sleep(T)

        if not (config.home / '.myqueue').is_dir():
            break

        try:
            with Queue(config) as queue:
                result = kick(queue, verbosity=0)
        except Exception:
            err.write_text(traceback.format_exc())
            break

        if result:
            with out.open('a') as fd:
                print(result, file=fd)

        pidfile.touch()

    pidfile.unlink()


def perform_daemon_action(config: Configuration, action: str) -> int:
    """Status of, stop or start daemon.

    Returns PID.
    """
    pidfile = config.home / f'.myqueue/daemon-{config.user}.pid'
    pid = -1

    running = is_running(pidfile)
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
                try:
                    os.kill(pid, signal.SIGWINCH)
                except ProcessLookupError:
                    pass
            else:
                print(f'You have to be on {host} in order to stop the daemon')
                return 1
        else:
            print('Not running!')

    elif action == 'start':
        if running:
            print('Already running')
        else:
            if pidfile.is_file():
                pidfile.unlink()
            start_daemon(config)
            while not pidfile.is_file():
                # Wait for the fork to start ...
                sleep(0.05)
            host, pid = read_hostname_and_pid(pidfile)
            print(f'PID: {pid}')

    else:
        assert False, action

    return pid
