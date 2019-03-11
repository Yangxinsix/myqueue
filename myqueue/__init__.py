from pathlib import Path
from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from .task import Task


__version__ = '19.2.1b1'


def submit(task: Task, verbosity: int = 1, dry_run: bool = False):
    from .runner import Runner
    with Runner(verbosity) as runner:
        runner.submit([task], dry_run)


def task(cmd: str,
         resources: str = '',
         args: List[str] = [],
         deps: Union[str, List[str], Task, List[Task]] = '',
         cores: int = 1,
         nodename: str = '',
         processes: int = 0,
         tmax: str = '10m',
         folder: str = '',
         workflow: bool = False,
         restart: int = 0,
         diskspace: float = 0.0) -> Task:
    """Create a Task object.

    ::

        task = task('abc.py')

    Parameters
    ----------
    cmd: str
        Command to be run.
    resources: str
        Resources::

            'cores[:nodename][:processes]:tmax'

        Examples: '48:1d', '32:1h', '8:xeon8:1:30m'.  Can not be used
        togeter with any of "cores", "nodename", "processes" and "tmax".
    args: list of str
        Command-line arguments or function arguments.
    deps: str, list of str, Task object  or list of Task objects
        Dependencies.  Examples: "task1,task2", "['task1', 'task2']".
    cores: int
        Number of cores (default is 1).
    nodename: str
        Name of node.
    processes: int
        Number of processes to start (default is one for each core).
    tmax: str
        Maximum time for task.  Examples: "40s", "30m", "20h" and "2d".
    folder: str
        Folder where task should run (default is current folder).
    workflow: bool
        Task is part of a workflow.
    restart: int
        How many times to restart task.
    diskspace: float
        Diskspace used.

    Returns
    -------
    Task
        Object representing the task.
    """

    from .commands import command
    from .resources import Resources, T

    path = Path(folder).absolute()

    dpaths = []
    if deps:
        if isinstance(deps, str):
            deps = deps.split(',')
        elif isinstance(deps, Task):
            deps = [deps]
        for dep in deps:
            if isinstance(dep, str):
                p = path / dep
                if '..' in p.parts:
                    p = p.parent.resolve() / p.name
                dpaths.append(p)
            else:
                dpaths.append(dep.dname)

    if '@' in cmd:
        cmd, resources = cmd.split('@')

    if resources:
        res = Resources.from_string(resources)
    else:
        res = Resources(cores, nodename, processes, T(tmax))

    return Task(command(cmd, args), res, dpaths, workflow, restart,
                int(diskspace), path)
