from pathlib import Path
from typing import Dict, Any  # noqa

config = {}  # type: Dict[str, Any]


def initialize_config(start: Path) -> None:
    if 'home' in config:
        return
    home = find_home_folder(start)
    config['home'] = home
    cfg = home / '.myqueue' / 'config.py'
    if cfg.is_file():
        namespace = {}  # type: Dict[str, Dict[str, Any]]
        exec(compile(cfg.read_text(), str(cfg), 'exec'), namespace)
        config.update(namespace['config'])


def find_home_folder(start: Path) -> Path:
    """Find closest .myqueue/ folder."""
    f = start
    while True:
        dir = f / '.myqueue'
        if dir.is_dir():
            if f == Path.home():
                break
            return f
        newf = f.parent
        if newf == f:
            break
        f = newf
    raise ValueError('Could not find .myqueue/ folder! '
                     'Please run "mq init"')
