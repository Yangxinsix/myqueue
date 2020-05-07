from pathlib import Path
from typing import Dict, Any, Set, List, Tuple

config: Dict[str, Any] = {}


def initialize_config(start: Path, force: bool = False) -> None:
    if not force and 'home' in config:
        return
    home = find_home_folder(start)
    config['home'] = home
    cfg = home / '.myqueue' / 'config.py'
    if cfg.is_file():
        namespace: Dict[str, Dict[str, Any]] = {}
        exec(compile(cfg.read_text(), str(cfg), 'exec'), namespace)
        config.update(namespace['config'])


def find_home_folder(start: Path) -> Path:
    """Find closest .myqueue/ folder."""
    f = start
    while True:
        dir = f / '.myqueue'
        if dir.is_dir():
            return f.absolute().resolve()
        newf = f.parent
        if newf == f:
            break
        f = newf
    raise ValueError('Could not find .myqueue/ folder!')


def guess_scheduler() -> str:
    import subprocess
    scheduler_commands = {'sbatch': 'slurm',
                          'bsub': 'lsf',
                          'qsub': 'pbs'}
    commands = []
    for command in scheduler_commands:
        if subprocess.run(['which', command],
                          stdout=subprocess.DEVNULL).returncode == 0:
            commands.append(command)
    if commands:
        assert len(commands) == 1
        scheduler = scheduler_commands[commands[0]]
    else:
        scheduler = 'local'
    return scheduler


def main(name=None):
    from .scheduler import get_scheduler
    from .utils import str2number

    folder = Path.home() / '.myqueue'
    if not folder.is_dir():
        folder.mkdir()

    name = name or guess_scheduler()
    scheduler = get_scheduler(name)
    nodelist = scheduler.get_config()
    nodelist.sort(key=lambda ncm: (-ncm[1], str2number(ncm[2])))
    nodelist2: List[Tuple[str, int, str]] = []
    done: Set[int] = set()
    for name, cores, memory in nodelist:
        if cores not in done:
            nodelist2.insert(len(done), (name, cores, memory))
            done.add(cores)
        else:
            nodelist2.append((name, cores, memory))
    cfg: Dict[str, Any] = {'scheduler': scheduler.name}
    if nodelist2:
        cfg['nodes'] = [(name, {'cores': cores, 'memory': memory})
                        for name, cores, memory in nodelist2]

    text = f'config = {cfg!r}\n'
    text = text.replace('= {', '= {\n    ')
    text = text.replace(", 'nodes'", ",\n    'nodes'")
    text = text.replace('(', '\n        (')
    text = '# generated with python3 -m myqueue.config\n' + text

    cfgfile = folder / 'config.py'
    if cfgfile.is_file():
        cfgfile.rename(cfgfile.with_name('config.py.old'))
    # cfgfile.write_text(text)
    print(text)


if __name__ == '__main__':
    import sys
    name = sys.argv[1]
    main(name)
