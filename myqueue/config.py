import os
from pathlib import Path
from typing import Dict, Any

_config = {}  # type: Dict[str, Any]


def read_config() -> Dict[str, Any]:
    if _config:
        return _config
    cfg = Path.home() / '.myqueue' / 'config.py'
    if cfg.is_file():
        namespace = {}  # type: Dict[str, Dict[str, Any]]
        exec(compile(cfg.read_text(), str(cfg), 'exec'), namespace)
        _config.update(namespace['config'])
    return _config


def home_folder() -> Path:
    dir = os.environ.get('MYQUEUE_HOME')
    if dir:
        return Path(dir)
    f = Path.cwd()
    while True:
        dir = f / '.myqueue'
        if dir.is_dir():
            return dir
        newf = f.parent
        if newf == f:
            break
        f = newf
    raise ValueError('Could not find your .myqueue/ folder!')
