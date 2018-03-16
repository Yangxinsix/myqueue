import time
from pathlib import Path
import numpy as np
from ase.parallel import world


def create(file, n):
    Path(file).write_text(str(n))


def timeout(file):
    n = int(Path(file).read_text())
    while n < 5:
        time.sleep(25)
        n += 1
        Path(file).write_text(str(n))


def memory():
    if world.size == 2:
        return
    x = []
    while True:
        print(len(x) * 8e-2)
        x.append(np.ones((10000, 1000)))
