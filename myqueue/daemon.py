import os
import subprocess
import sys
from time import sleep, time
from pathlib import Path

T = 600

out = Path.home() / '.myqueue/daemon.out'
err = Path.home() / '.myqueue/daemon.err'


def run() -> bool:
    assert not err.is_file()
    if out.is_file():
        age = time() - out.stat().st_mtime
    else:
        out.write_text('')
        age = 2 * T
    if age < 1.5 * T:
        return False

    pid = os.fork()
    if pid == 0:
        pid = os.fork()
        if pid == 0:
            if 1:
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
    while not err.is_file():
        sleep(T)
        result = subprocess.run(f'python3 -m myqueue kick --all >> {out}',
                                shell=True,
                                stderr=subprocess.PIPE)
        if result.returncode:
            err.write_bytes(result.stderr)
            break


if __name__ == '__main__':
    print(run())
