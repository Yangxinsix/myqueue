import subprocess
from typing import List

import pytest
from myqueue.config import Configuration


def check_output(args: List[str]) -> bytes:
    return b'This is Intel'


def test_config(monkeypatch):
    monkeypatch.setattr(subprocess, 'check_output', check_output)
    cfg = Configuration('test')
    print(cfg)
    cfg.print()
    assert cfg.mpi_implementation == 'intel'


def test_deprecated_key(mq):
    cfg_file = mq.config.home / '.myqueue/config.py'
    cfg_file.write_text('config = {}\n')
    with pytest.raises(ValueError):
        Configuration.read()
    cfg_file.write_text("config = {'scheduler': 'test', 'mpi': 'openmpi'}\n")
    with pytest.warns(UserWarning):
        cfg = Configuration.read()
    assert cfg.mpi_implementation == 'openmpi'
