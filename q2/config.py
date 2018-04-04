import os
from pathlib import Path
from typing import Dict

_config = {}  # type: Dict[str, Dict]


def read_config():
    cfg = Path.home() / '.q2' / 'config.py'
    if cfg.is_file():
        namespace = {}
        exec(compile(cfg.read_text(), cfg, 'exec'), namespace)
        _config.update(namespace['config'])
    return _config


def home_folder():
    dir = os.environ.get('Q2_HOME')
    if dir:
        return Path(dir)
    return Path.home() / '.q2'
