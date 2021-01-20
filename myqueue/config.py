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
    """Try different scheduler commands to guess the correct scheduler."""
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
        if len(commands) > 1:
            raise ValueError('Please specify a scheduler: ' +
                             ', '.join(scheduler_commands[cmd]
                                       for cmd in commands))
        scheduler = scheduler_commands[commands[0]]
    else:
        scheduler = 'local'
    return scheduler


def guess_configuration(scheduler_name: str = '',
                        queue_name: str = '',
                        in_place: bool = False) -> None:
    """Simple auto-config tool.

    Creates a config.py file.
    """
    from .scheduler import get_scheduler
    from .utils import str2number

    folder = Path.home() / '.myqueue'
    if not folder.is_dir():
        folder.mkdir()

    name = scheduler_name or guess_scheduler()
    scheduler = get_scheduler(name)
    nodelist, extra_args = scheduler.get_config(queue_name)
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
    if extra_args:
        cfg['extra_args'] = extra_args

    text = f'config = {cfg!r}\n'
    text = text.replace('= {', '= {\n    ')
    text = text.replace(", 'nodes'", ",\n    'nodes'")
    text = text.replace(", 'extra_args'", ",\n    'extra_args'")
    text = text.replace('(', '\n        (')
    text = '# generated with mq config\n' + text

    if in_place:
        cfgfile = folder / 'config.py'
        if cfgfile.is_file():
            cfgfile.rename(cfgfile.with_name('config.py.old'))
        cfgfile.write_text(text)
    else:
        print(text)
