import subprocess
from typing import List

from myqueue.config import Configuration


def check_output(args: List[str]) -> bytes:
    return b'This is Intel'


def test_config(monkeypatch):
    monkeypatch.setattr(subprocess, 'check_output', check_output)
    cfg = Configuration('test')
    print(cfg)
    cfg.print()
    assert cfg.mpi_implementation == 'intel'
