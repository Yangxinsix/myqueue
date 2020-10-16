from myqueue.complete import complete


def test_ls():
    words = complete('-', 'ls', 'mq ls -', 7)
    assert '--not-recursive' in words


def test_daemon():
    words = complete('', 'daemon', 'mq daemon ', 9)
    assert 'start' in words


def test_rm():
    words = complete('', 'mq', 'mq ', 3)
    assert 'rm' in words
