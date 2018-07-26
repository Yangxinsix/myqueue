import sys


def oom(local=True):
    try:
        from ase.parallel import world
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
