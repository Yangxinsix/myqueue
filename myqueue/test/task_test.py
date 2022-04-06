from pathlib import Path
from types import SimpleNamespace

import pytest
from myqueue.states import State
from myqueue.task import task as create_task


def test_task(tmp_path):
    t = create_task('x', folder=tmp_path)
    assert t.name == 'x.0'
    assert t.int_id == 0

    t.state = State.running
    assert t.running_time(1.0) == 1.0

    assert repr(t) == 'Task(x)'

    for c in 'ifnAraste':
        x = t.order(c)
        assert not (x < x)

    with pytest.raises(ValueError):
        t.order('x')

    # id, folder, name, resources, state, restart, workflow, diskspace,
    # deps, creates, t1, t2, t3, error, memory_usage
    line = ('0,/home/jensj/,x.py,1:1h,done,'
            '0,1,0,,,'
            '2021-07-09 17:04:52,2021-07-09 17:25:16,2021-07-09 17:39:44,'
            ',10MB')
    assert t.fromcsv(line.split(',')).memory_usage == 0

    dct = {'id': '0',
           'folder': str(tmp_path),
           'cmd': {'args': [], 'type': 'python-module', 'cmd': 'x'},
           'state': 'running',
           'resources': {'cores': 1},
           'restart': 0,
           'workflow': False,
           'deps': [],
           'diskspace': 0,
           'notifications': '',
           'creates': [],
           'tqueued': 0.0,
           'trunning': 0.0,
           'tstop': 0.0,
           'error': '',
           'user': t.user}
    assert t.todict() == dct

    del dct['diskspace']
    del dct['creates']
    del dct['restart']
    t.fromdict(dct, Path())

    (t.folder / f'{t.cmd.fname}.done').write_text('')
    assert t.read_state_file() == State.done
    (t.folder / f'{t.cmd.fname}.FAILED').write_text('')
    assert t.read_state_file() == State.FAILED

    err = tmp_path / 'x.err'

    def oom():
        return t.read_error(
            SimpleNamespace(error_file=lambda _: err))  # type: ignore

    assert not oom()
    err.write_text('... memory limit at some point.')
    assert oom()
    err.write_text('... malloc ...')
    assert oom()
    err.write_text('MemoryError ...')
    assert oom()
    err.write_text('... oom-kill ...')
    assert oom()
    err.write_text('... out of memory')
    assert oom()
    err.write_text('... some other error ...')
    assert not oom()

    t.folder = t.folder / 'missing'
    t.write_state_file()
