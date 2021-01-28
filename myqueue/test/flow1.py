from myqueue.workflow import run


def f1(x: int) -> int:
    print(x)
    return x + 1


def f2(*X: int) -> int:
    print(X)
    return max(X)


def workflow(wrap):
    A = []
    for x in range(3):
        a = wrap(f1, cores=1, name=f'f1-{x}')(x)
        A.append(a)

    b = wrap(f2)(*A)

    if b > 2:
        wrap(print)(b)

    return b


if __name__ == '__main__':
    workflow(run)
