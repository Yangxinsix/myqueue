import time
from pathlib import Path


def create(file, n):
    Path(file).write_text(str(n))


def memory():
    import numpy as np
    from ase.parallel import world
    if world.size > 1:
        return
    x = []
    while True:
        print(len(x) * 8e-2)
        x.append(np.ones((10000, 1000)))


def fail(t):
    time.sleep(t)
    print(1 / 0)
