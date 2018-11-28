from pathlib import Path
from typing import Dict, Any  # noqa

config = {}  # type: Dict[str, Any]


def initialize_config() -> None:
    home = find_home_folder()
    config['home'] = home
    cfg = home / 'config.py'
    if cfg.is_file():
        namespace = {}  # type: Dict[str, Dict[str, Any]]
        exec(compile(cfg.read_text(), str(cfg), 'exec'), namespace)
        config.update(namespace['config'])


def find_home_folder() -> Path:
    """Find closest .myqueue/ folder."""
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
