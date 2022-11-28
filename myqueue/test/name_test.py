from pathlib import Path
from myqueue.workflow import run


def test_name(mq):
    Path('dir').mkdir()
    mq('submit hello.sh -n helloworld dir')
    mq('ls -n helloworld')
    mq('rm -n helloworld dir -s aA')
    assert mq.wait() == ''


def workflow():
    with run(function=print, name='T1'):
        run(function=print, name='T2')


def test_name_dep(mq):
    dir = Path('dir')
    dir.mkdir()
    wf = Path(__file__)
    mq(f'workflow {wf} dir')
    assert mq.wait() == 'dd'
    mq(f'workflow {wf} dir')
    assert mq.states() == 'dd'
    mq('rm -n T2 -s d dir --force')
    mq('ls')
    mq(f'workflow {wf} dir')
    assert mq.states() == 'd'
    (dir / 'T2.result').unlink()
    mq(f'workflow {wf} dir')
    assert mq.wait() == 'dd'
