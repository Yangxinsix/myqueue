import json
from pathlib import Path

_config = {}


def read_config():
    cfg = Path.home() / '.q2' / 'config.py'
    if cfg.is_file():
        namespace = {}
        exec(compile(cfg.read_text(), cfg, 'exec'), namespace)
        _config.update(namespace['config'])
    return _config
