from myqueue.pretty import pprint
from myqueue.task import create_task
import pytest


@pytest.mark.xfail
def test_pretty(capsys):
    pprint([create_task('abc')] * 10, maxlines=4, columns='i-')
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 9
