from myqueue.complete import complete


def test_ls():
    words = complete('-', 'ls', 'mq ls -', 7)
    assert '--not-recursive' in words
