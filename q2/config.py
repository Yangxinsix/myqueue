import json
from pathlib import Path
_config = {}


def read_config():
    if not _config:
        cfg = Path.home() / '.q2' / 'config.json'
        if cfg.is_file():
            _config.update(json.loads(cfg.read_text()))
    return _config


def write_config(cfg):
    cfg = Path.home() / '.q2' / 'config.json'
    cfg.write_text(json.dumps(_config))
