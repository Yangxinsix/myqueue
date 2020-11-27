import ast
import runpy
from pathlib import Path
from functools import partial
from typing import Callable, List, Dict, Any, Union

from .progress import progress_bar
from .task import Task
from .utils import chdir, plural
from myqueue.commands import create_command, WorkflowTask
from myqueue.resources import Resources

DEFAULT_VERBOSITY = 1


def workflow(args,
             folders: List[Path],
             verbosity: int = DEFAULT_VERBOSITY) -> List[Task]:
    """Collect tasks from workflow script(s) and folders."""
    if args.arguments:
        kwargs = str2kwargs(args.arguments)
    else:
        kwargs = {}

    if args.pattern:
        pattern = args.script
        tasks = workflow_from_scripts(pattern,
                                      kwargs,
                                      folders,
                                      verbosity=verbosity)
    else:
        tasks = workflow_from_script(args.script,
                                     kwargs,
                                     folders,
                                     verbosity=verbosity)

    if args.targets:
        names = args.targets.split(',')
        tasks = filter_tasks(tasks, names)

    tasks = [task for task in tasks if not task.skip()]

    for task in tasks:
        task.workflow = True

    return tasks


def get_workflow_function(path, kwargs):
    module = runpy.run_path(path)
    try:
        func = module['workflow']
    except AttributeError:
        func = module['create_tasks']
    if kwargs:
        name = func.__name__
        func = partial(func, **kwargs)
        func.__name__ = name
    func.path = path
    return func


def workflow_from_scripts(
        pattern: str,
        kwargs: Dict[str, Any],
        folders: List[Path],
        verbosity: int = DEFAULT_VERBOSITY) -> List[Task]:
    """Generate tasks from workflows defined by '**/*{script}'."""
    tasks: List[Task] = []
    paths = [path
             for folder in folders
             for path in folder.glob('**/*' + pattern)]
    pb = progress_bar(len(paths),
                      f'Scanning {len(paths)} scripts:',
                      verbosity)

    for path in paths:
        func = get_workflow_function(path, kwargs)
        tasks += get_tasks_from_folder(path.parent, func)
        next(pb)
    return tasks


def workflow_from_script(script,
                         kwargs,
                         folders: List[Path],
                         verbosity: int = DEFAULT_VERBOSITY) -> List[Task]:
    """Collect tasks from workflow defined in python script."""
    func = get_workflow_function(script, kwargs)

    tasks: List[Task] = []

    n_folders = plural(len(folders), 'folder')
    pb = progress_bar(len(folders),
                      f'Scanning {n_folders}:',
                      verbosity)
    for folder in folders:
        tasks += get_tasks_from_folder(folder, func)
        next(pb)

    return tasks


def filter_tasks(tasks: List[Task], names: List[str]) -> List[Task]:
    """Filter tasks that are not in names or in dependencies of names."""
    include = set()
    map = {task.dname: task for task in tasks}
    for task in tasks:
        if task.cmd.name in names:
            for t in task.ideps(map):
                include.add(t)
    filteredtasks = list(include)
    return filteredtasks


def str2kwargs(args: str) -> Dict[str, Union[int, str, bool, float]]:
    """Convert str to dict.

    >>> str2kwargs('name=hello,n=5')
    {'name': 'hello', 'n': 5}
    """
    kwargs = {}
    for arg in args.split(','):
        key, value = arg.split('=')
        try:
            v = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            v = value
        kwargs[key] = v
    return kwargs


def get_tasks_from_folder(folder: Path,
                          func: Callable) -> List[Task]:
    """Collect tasks from folder."""
    with chdir(folder):
        if func.__name__ == 'create_tasks':
            tasks = func()
        else:
            script = func.path
            tasks = collect_tasks_from_workflow_function(folder, script, func)

    return tasks


class StopWorkflow(Exception):
    ''


def collect_tasks_from_workflow_function(folder,
                                         script,
                                         func: Callable[[Callable], None]
                                         ) -> List[Task]:

    tasks = {}
    collect = partial(run, folder, script, tasks)
    try:
        func(collect)
    except StopWorkflow:
        pass
    print(run.tasks)
    return list(run.tasks.values())


def run(folder,
        script,
        tasks,
        cmd,
        *args,
        kwargs={},
        name=None,
        block=False,
        done=False,
        resources=None,
        cores=0,
        nodename='',
        processes=0,
        tmax='',
        restart=0,
        diskspace=0,
        creates=[],
        deps=None,
        **kws):

    if block and not done:
        raise StopWorkflow

    kws.update(kwargs)

    dependencies = set()
    for arg in list(args) + list(kws.values()) + (deps or []):
        if isinstance(arg, Result):
            dependencies.add(arg.task)

    if isinstance(cmd, str):
        command = create_command(cmd, args, name=name)
        name = command.name
    else:
        if name is None:
            name = get_name(cmd, args, kwargs)
        command = WorkflowTask(script, name)

    res = Resources.from_args_and_command(
        cores, nodename, processes, tmax,
        resources, command, folder)

    task = Task(command,
                deps=list(dependencies),
                resources=res,
                workflow=True,
                restart=restart,
                diskspace=diskspace,
                folder=folder,
                creates=creates)

    assert name not in tasks
    tasks[name] = task

    return Result(task)


class Result:
    def __init__(self, task):
        self.task = task

    def __getitem__(self, key):
        return self

    def __getattr__(self, attr):
        return self


def get_name(func, args, kwargs):
    return f'{func.__module__}.{func.__name__}'
