from myqueue.workflow import run, wrap


def f1(x: int) -> int:
    print(x)
    return x + 1


def f2(*X: int) -> int:
    print(X)
    return max(X)


def workflow():
    A = []
    for x in range(3):
        with run(function=f1, cores=1, name=f'f1-{x}', args=[x]) as a:
            wrap(f1)(a.result)
            A.append(a)

    b = wrap(f2, tmax='1h')(*A)

    if b > 2:
        wrap(print)(b)

    return b


if __name__ == '__main__':
    workflow()
