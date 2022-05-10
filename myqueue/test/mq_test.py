from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest
from myqueue.queue import Queue
from myqueue.task import task
from myqueue.states import State
from ..utils import chdir
from myqueue.cli import _main

LOCAL = True


def test_submit_args(mq):
    mq('''submit "myqueue.test.mod --opt={...,x={'y':(1,2)}"''')
    mq.wait()
    assert mq.states() == 'd'


def test_submit(mq):
    f = Path('folder')
    f.mkdir()
    mq('submit time@sleep+0.1 . folder --max-tasks=9')
    mq('submit shell:echo+hello -d time@sleep+0.1')
    mq.wait()
    assert mq.states() == 'ddd'
    shutil.rmtree(f)
    mq('sync -z')
    mq('sync')
    assert mq.states() == 'dd'
    mq('daemon status')


def test_fail(mq):
    mq('submit time@sleep+a')
    mq('submit shell:echo+hello -d time@sleep+a')
    mq('submit shell:echo+hello2 -d shell:echo+hello')
    mq.wait()
    mq('info')
    mq('info -i1 -v')
    mq('ls -S t')
    mq('ls -L')
    assert mq.states() == 'FCC', mq.states()
    mq('resubmit -sF . -z')
    assert mq.states() == 'FCC'
    mq('resubmit -sF .')
    mq.wait()
    assert mq.states() == 'CCF'
    mq('modify -s F -N T .')
    assert mq.states() == 'CCT'


def test_fail2(mq):
    mq('submit time@sleep+a --workflow')
    mq.wait()
    assert mq.states() == 'F'
    mq('remove --states F .')
    mq('submit time@sleep+a --workflow')
    mq.wait()
    assert mq.states() == ''


def test_timeout(mq):
    t = 3 if LOCAL else 120
    mq(f'submit -n zzz "shell:sleep {t}" -R 1:1s')
    mq('submit "shell:echo hello" -d zzz')
    mq.wait()
    mq('resubmit -sT . -R 1:5m')
    mq.wait()
    assert mq.states() == 'Cd'


def test_timeout2(mq):
    t = 3 if LOCAL else 120
    mq(f'submit "shell:sleep {t}" -R1:{t // 3}s --restart 2')
    mq(f'submit "shell:echo hello" -d shell:sleep+{t}')
    mq.wait()
    mq('ls')
    mq('kick')
    mq('ls')
    mq.wait()
    if mq.states() != 'dd':
        mq('kick')
        mq.wait()
        assert mq.states() == 'dd'


def test_oom(mq):
    mq(f'submit "myqueue.test@oom {LOCAL}" --restart 2')
    mq.wait()
    assert mq.states() == 'M'
    mq('kick')
    mq.wait()
    assert mq.states() == 'd'


def test_cancel(mq):
    mq('submit shell:sleep+2')
    mq('submit shell:sleep+999')
    mq('submit shell:echo+hello -d shell:sleep+999')
    mq('rm -n shell:sleep+999 -srq .')
    mq.wait()
    assert mq.states() == 'd'


def test_check_dependency_order(mq):
    mq('submit myqueue.test@timeout_once -R 1:1s --restart 1')
    mq('submit shell:echo+ok -d myqueue.test@timeout_once --restart 1')
    mq.wait()
    assert mq.states() == 'TC'
    mq('kick -z')
    mq('kick')
    mq.wait()
    assert mq.states() == 'dd'


def test_run(mq):
    mq('run "math@sin 3.14" . -z')
    mq('run "math@sin 3.14" .')
    mq('submit "time@sleep 1"')
    mq('run "time@sleep 1" .')
    mq.wait()
    assert mq.states() == ''


def test_misc(mq):
    f = Path('subfolder')
    f.mkdir()
    with chdir(f):
        mq('init')
        mq('init')
    mq('help')
    mq('ls -saA')
    mq('-V')
    mq('completion')
    mq('completion -v')
    mq('ls no_such_folder', error=1)
    mq('')
    mq('info -A')


def test_sync_kick(mq):
    mq('sync')
    mq('kick')


def test_slash(mq):
    mq('submit "shell:echo a/b"')
    mq('submit "shell:echo a/c" -w')
    mq.wait()
    assert mq.states() == 'dd'


def test_config(mq):
    mq('config local')


def test_more_homes(mq):
    f = Path('folder')
    f.mkdir()
    with chdir(f):
        mq('init')
    mq('submit shell:echo . folder', error=1)


def test_permission_error(mq):
    try:
        (mq.config.home / '.myqueue').chmod(0o500)  # r-x
        mq('ls')
    finally:
        (mq.config.home / '.myqueue').chmod(0o700)  # rwx


def test_failing_scheduler(mq):
    with pytest.raises(RuntimeError):
        # Special argument that makes test-scheduler raise an error:
        mq('submit "time.sleep FAIL"')
    mq.wait()
    assert mq.states() == ''


@pytest.mark.xfail
def test_ctrl_c(mq):
    # Special argument that makes test-scheduler raise an error:
    mq('submit "time.sleep SIMULATE-CTRL-C"')
    mq.wait()
    assert mq.states() == 'd'


def test_sync_cancel(mq):
    with Queue(mq.config, verbosity=0) as q:
        t = task('shell:echo')
        t.state = State.running
        t.trunning = time.time()
        q.tasks.append(t)
        q.changed.add(t)
    mq('sync')
    assert mq.states() == 'C'


def test_hold_release(mq):
    mq('submit shell:echo+hello')
    mq('modify -s q -N h . -z')
    mq('modify -s q -N h .')
    mq.wait()
    assert mq.states() == 'h'
    mq('modify -s h -N q . -z')
    mq('modify -s h -N q .')
    mq.wait()
    assert mq.states() == 'd'
    with pytest.raises(ValueError):
        mq('modify -s d -N q .')


def test_clean_up(mq):
    with Queue(mq.config, verbosity=0) as q:
        t1 = task('shell:echo')
        t1.state = State.running
        t1.trunning = 0.0  # very old
        t2 = task('shell:echo', deps=[t1])
        t2.state = State.queued
        q.tasks += [t1, t2]
        q.changed.add(t1)
    assert mq.states() == 'TC'


def test_cli_exception(mq, monkeypatch):
    def run(args, test):
        raise ValueError

    monkeypatch.setattr('myqueue.cli.run', run)

    # With --traceback:
    with pytest.raises(ValueError):
        mq('ls')

    # Without --traceback:
    assert _main(['ls']) == 1


def test_mq_exception(mq):
    mq('rm', error=1)
    mq('ls -i 0 -s q', error=1)
    with pytest.raises(ValueError):
        mq('ls -i 0 .')
    mq('rm .', error=1)
