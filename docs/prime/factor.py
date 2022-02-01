from __future__ import annotations
import json
from pathlib import Path


def factor(x: int) -> list[int]:
    for f in range(2, x // 2 + 1):
        if x % f == 0:
            return [f] + factor(x // f)
    return [x]


if __name__ == '__main__':
    x = int(Path.cwd().name)  # name of current folder
    factors = factor(x)
    Path('factors.json').write_text(json.dumps({'factors': factors}))
