from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest
from myqueue.queue import Queue, sort_out_dependencies
from myqueue.task import task
from myqueue.states import State
from myqueue.utils import chdir, get_states_of_active_tasks
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
    assert mq.wait() == 'ddd'
    shutil.rmtree(f)
    mq('sync -z')
    mq('sync')
    assert mq.states() == 'dd'
    mq('daemon status')
    assert get_states_of_active_tasks() == {}


def test_fail(mq):
    mq('submit time@sleep+a')
    mq('submit shell:echo+hello -d time@sleep+a')
    mq('submit shell:echo+hello2 -d shell:echo+hello')
    mq.wait()
    mq('info')
    mq('info -i1 -v')
    mq('ls -S t')
    assert mq.states() == 'FCC', mq.states()
    mq('resubmit -sF . -z')
    assert mq.states() == 'FCC'
    mq('resubmit -sF . --remove')
    assert mq.wait() == 'CCF'


def test_fail2(mq):
    mq('submit time@sleep+a --workflow')
    mq.wait()
    assert mq.states() == 'F'
    mq('remove --states F --force .')
    mq('submit time@sleep+a --workflow')
    assert mq.wait() == 'F'


def test_timeout(mq):
    t = 3 if LOCAL else 120
    mq(f'submit -n zzz "shell:sleep {t}" -R 1:1s')
    mq('submit "shell:echo hello" -d zzz')
    mq.wait()
    mq('resubmit -sT . -R 1:5m --remove')
    assert mq.wait() == 'Cd'


def test_timeout2(mq):
    t = 3 if LOCAL else 120
    mq(f'submit "shell:sleep {t}" -R1:{t // 3}s --restart 3')
    mq(f'submit "shell:echo hello" -d shell:sleep+{t}')
    mq.wait()
    mq('ls')
    mq('kick')
    mq('ls')
    mq.wait()
    mq('kick')
    q = mq.wait()
    if q == 'TCTCTC':
        # on slow systems we need another kick:
        mq('kick')
        q = mq.wait()[2:]
    assert q == 'TCTCdd'


def test_oom(mq):
    mq(f'submit "myqueue.test@oom {LOCAL}" --restart 2')
    assert mq.wait() == 'M'
    mq('kick')
    assert mq.wait() == 'Md'


def test_cancel(mq):
    mq('submit shell:sleep+2')
    mq('submit shell:sleep+999')
    mq('submit shell:echo+hello -d shell:sleep+999')
    mq('rm -n shell:sleep+999 -srq .')
    assert mq.wait() == 'dC'


def test_check_dependency_order(mq):
    mq('submit myqueue.test@timeout_once -R 1:5s --restart 1')
    mq('submit shell:echo+ok -d myqueue.test@timeout_once --restart 1')
    assert mq.wait() == 'TC'
    mq('kick -z')
    mq('kick')
    assert mq.wait() == 'TCdd'


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
    assert mq.wait() == 'dd'


def test_config(mq):
    mq('config local')


def test_more_homes(mq):
    f = Path('folder')
    f.mkdir()
    with chdir(f):
        mq('init')
    mq('submit shell:echo . folder', error=1)


def test_permission_error(mq):
    mq('ls')
    try:
        (mq.config.home / '.myqueue').chmod(0o500)  # r-x
        mq('ls')
    finally:
        (mq.config.home / '.myqueue').chmod(0o700)  # rwx


def test_failing_scheduler(mq):
    with pytest.raises(RuntimeError):
        # Special argument that makes test-scheduler raise an error:
        mq('submit "time.sleep FAIL"')
    assert mq.wait() == ''


@pytest.mark.xfail
def test_ctrl_c(mq):
    # Special argument that makes test-scheduler raise an error:
    mq('submit "time.sleep SIMULATE-CTRL-C"')
    assert mq.wait() == 'd'


def test_sync_cancel(mq):
    with Queue(mq.config) as q:
        t = task('shell:echo')
        t.state = State.running
        t.trunning = time.time()
        q.add(t)
    mq('sync')
    assert mq.states() == ''


def test_hold_release(mq):
    mq('submit shell:echo+hello')
    mq('modify -s q -N h . -z')
    mq('modify -s q -N h .')
    assert mq.wait() == 'h'
    (name, state), = get_states_of_active_tasks().items()
    assert state == 'h'
    assert name == './shell:echo+hello'

    mq('modify -s h -N q . -z')
    mq('modify -s h -N q .')
    assert mq.wait() == 'd'
    with pytest.raises(ValueError):
        mq('modify -s d -N q .')


def test_clean_up(mq):
    with Queue(mq.config) as q:
        t1 = task('shell:echo+1')
        t1.id = 1
        t1.state = State.running
        t1.trunning = 0.0  # very old
        t2 = task('shell:echo+2', deps=[t1])
        t2.state = State.queued
        t2.id = 2
        sort_out_dependencies([t1, t2], q)
        q.add(t1, t2)
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
    mq('ls -i 0')
    mq('ls -i 0 -s q', error=1)
    with pytest.raises(ValueError):
        mq('ls -i 0 .')
    mq('rm .', error=1)
