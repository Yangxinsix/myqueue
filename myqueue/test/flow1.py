from typing import List
from myqueue.workflow import nowrap


def f1(x: int) -> int:
    print(x)
    return x + 1


def f2(*X: List[int]) -> int:
    print(X)
    return max(X)


def workflow(wrap):
    A = []
    for x in range(3):
        a = wrap(f1, cores=1, name=f'f1-{x}')(x)
        A.append(a)

    a = wrap(f2, deps=A)(*A)

    if a > 2:
        wrap(print)(a)


if __name__ == '__main__':
    workflow(nowrap)
