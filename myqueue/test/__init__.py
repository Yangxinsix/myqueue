import sys
import time
from pathlib import Path


def oom(local: bool = True) -> None:
    try:
        from ase.parallel import world  # type: ignore
        if world.size > 1:
            return
    except ImportError:
        pass
    if local:
        print('error: exceeded memory limit at some point.', file=sys.stderr)
        raise MemoryError
    x = 'x'
    while True:
        print(len(x))
        x = x + x


def timeout_once():
    path = Path('timeout_once.out')
    if not path.is_file():
        path.touch()
        time.sleep(1000)
