from pathlib import Path


def test_name(mq):
    Path('dir').mkdir()
    mq('submit hello.sh -n helloworld dir')
    mq('ls -n helloworld')
    mq('rm -n helloworld dir -s aA')
    assert mq.wait() == ''
