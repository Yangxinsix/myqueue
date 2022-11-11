from pathlib import Path
from types import SimpleNamespace

import pytest
from myqueue.states import State
from myqueue.task import create_task


def test_task(tmp_path):
    t = create_task('x', folder=tmp_path)
    assert t.name == 'x.0'
    assert t.id == 0

    t.state = State.running
    assert t.running_time(1.0) == 1.0

    assert repr(t) == 'Task(x)'

    for c in 'ifnAraste':
        x = t.order_key(c)
        assert not (x < x)

    with pytest.raises(ValueError):
        t.order_key('x')

    dct = {'id': 0,
           'folder': str(tmp_path),
           'cmd': {'args': [], 'type': 'python-module', 'cmd': 'x'},
           'state': 'running',
           'resources': {'cores': 1},
           'restart': 0,
           'workflow': False,
           'deps': [],
           'notifications': '',
           'creates': [],
           'tqueued': 0.0,
           'trunning': 0.0,
           'tstop': 0.0,
           'error': '',
           'user': t.user}
    assert t.todict() == dct

    del dct['creates']
    del dct['restart']
    t.fromdict(dct, Path())

    err = tmp_path / 'x.err'

    def oom():
        return t.read_error_and_check_for_oom(
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
