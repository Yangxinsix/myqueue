from myqueue.workflow import run as run0, wrap, resources


def run(**kwargs):
    return run0(args=['hello', 'world'], **kwargs)


@resources(tmax='1m')
def workflow():
    with run(shell='echo', ):
        with run(module='myqueue.test.hello'):
            with resources(tmax='2m'):
                with run(function=print, name='p1'):
                    with run(script=__file__, tmax='3m'):
                        with run(script='hello.sh'):
                            wrap(print)('hello', 'world')


def __init__(self):
    import sys
    print(*sys.argv[1:])
