import os
from pathlib import Path
from typing import Dict, Any  # noqa

_config = {}  # type: Dict[str, Dict]


def read_config() -> Dict[str, Dict[str, Any]]:
    cfg = Path.home() / '.myqueue' / 'config.py'
    if cfg.is_file():
        namespace = {}  # type: Dict[str, Any]
        exec(compile(cfg.read_text(), str(cfg), 'exec'), namespace)
        _config.update(namespace['config'])
    return _config


def home_folder() -> Path:
    dir = os.environ.get('MYQUEUE_HOME')
    if dir:
        return Path(dir)
    return Path.home() / '.myqueue'
