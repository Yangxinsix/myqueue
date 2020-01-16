import shutil
import time
from pathlib import Path

from .runner import test, mq, wait, states, LOCAL, mqlist
from ..utils import chdir


@test
def submit():
    f = Path('folder')
    f.mkdir()
    mq('submit time@sleep+2 . folder --max-tasks=9')
    mq('submit shell:echo+hello -d time@sleep+2')
    wait()
    assert states() == 'ddd'
    shutil.rmtree(f)
    mq('sync')
    assert states() == 'dd'
    mq('daemon status')


@test
def fail():
    mq('submit time@sleep+a')
    mq('submit shell:echo+hello -d time@sleep+a')
    mq('submit shell:echo+hello2 -d shell:echo+hello')
    wait()
    id = mqlist()[0].id
    mq(f'info {id} -v')
    mq('ls -S t')
    # mq('ls -AC')
    mq('ls -L')
    assert states() == 'FCC', states()
    mq('resubmit -sF . -z')
    assert states() == 'FCC'
    mq('resubmit -sF .')
    wait()
    assert states() == 'CCF'
    mq('modify -s F T .')
    assert states() == 'CCT'


@test
def fail2():
    mq('submit time@sleep+a --workflow')
    wait()
    assert states() == 'F'
    mq('remove --states F .')
    mq('submit time@sleep+a --workflow')
    wait()
    assert states() == ''


@test
def timeout():
    t = 3 if LOCAL else 120
    mq(f'submit -n zzz "shell:sleep {t}" -R 1:1s')
    mq('submit "shell:echo hello" -d zzz')
    wait()
    mq('resubmit -sT . -R 1:5m')
    wait()
    assert states() == 'Cd'


@test
def timeout2():
    t = 3 if LOCAL else 120
    mq(f'submit "shell:sleep {t}" -R1:{t // 3}s --restart 2')
    mq(f'submit "shell:echo hello" -d shell:sleep+{t}')
    wait()
    mq('kick')
    wait()
    if states() != 'dd':
        mq('kick')
        wait()
        assert states() == 'dd'


@test
def oom():
    mq(f'submit "myqueue.test@oom {LOCAL}" --restart 2')
    wait()
    assert states() == 'M'
    mq('kick')
    wait()
    assert states() == 'd'


wf = """
from myqueue.task import task
def create_tasks():
    t1 = task('shell:sleep+3')
    return [t1, task('shell:touch+hello', deps=[t1], creates=['hello'])]
"""


@test
def workflow():
    mq('submit shell:sleep+3@1:1m -w')
    time.sleep(2)
    Path('wf.py').write_text(wf)
    mq('workflow wf.py . -t shell:touch+hello')
    wait()
    assert states() == 'dd'


wf2 = """
from myqueue.task import task
def create_tasks():
    return [task('shell:echo+hi', diskspace=1) for _ in range(4)]
"""


@test
def workflow2():
    Path('wf2.py').write_text(wf2)
    mq('workflow wf2.py .')
    mq('kick')
    wait()
    assert states() == 'dddd'


@test
def cancel():
    mq('submit shell:sleep+2')
    mq('submit shell:sleep+999')
    mq('submit shell:echo+hello -d shell:sleep+999')
    mq('rm -n shell:sleep+999 -srq .')
    wait()
    assert states() == 'd'


@test
def check_dependency_order():
    mq('submit myqueue.test@timeout_once -R 1:1s --restart 1')
    mq('submit shell:echo+ok -d myqueue.test@timeout_once --restart 1')
    wait()
    assert states() == 'TC'
    mq('kick')
    wait()
    assert states() == 'dd'


@test
def run():
    mq('run "math@sin 3.14" . -z')
    mq('run "math@sin 3.14" .')
    mq('submit "time@sleep 1"')
    mq('run "time@sleep 1" .')
    wait()
    assert states() == ''


@test
def misc():
    f = Path('subfolder')
    f.mkdir()
    with chdir(f):
        mq('init')
    mq('help')
    mq('ls -saA')
    mq('-V')


@test
def slash():
    mq('submit "shell:echo a/b"')
    mq('submit "shell:echo a/c" -w')
    wait()
    assert states() == 'dd'
