import ast
import runpy
import sys
from pathlib import Path
from functools import partial
from typing import Callable, List, Dict, Any, Union

from .progress import progress_bar
from .task import Task
from .utils import chdir, plural
from myqueue.commands import WorkflowTask
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
    except KeyError:
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
            tasks = collect(func, folder)

    return tasks


class StopCollecting(Exception):
    ''


class StopRunning(Exception):
    ''


class Result:
    def __init__(self, task):
        self.task = task

    def __getitem__(self, key):
        return self

    def __getattr__(self, attr):
        return self

    def __gt__(self, other):
        raise StopCollecting

    __lt__ = __gt__


def get_name(func):
    return f'{func.__module__}.{func.__name__}'


def nowrap(function, **kwargs):
    return function


class Cached:
    def __init__(self, function, name):
        self.function = function
        self.path = Path(f'{name}.done')

    def is_done(self, *args, **kwargs):
        return self.path.is_file()

    def __call__(self, *args, **kwargs):
        if self.is_done():
            return eval(self.path.read_text())
        result = self.function(*args, **kwargs)
        self.path.write_text(repr(result))
        return result


class Collector:
    def __init__(self):
        self.tasks = {}

    def collect(self,
                function,
                *,
                name=None,
                deps=None,
                **run_kwargs):
        name = name or get_name(function)

        if not hasattr(function, 'is_done'):
            function = Cached(function, name)

        def wrapper(*args, **kwargs):
            if function.is_done(*args, **kwargs):
                return function(*args, **kwargs)

            dependencies = set()
            for arg in list(args) + list(kwargs.values()) + (deps or []):
                if isinstance(arg, Result):
                    dependencies.add(arg.task[0])

            task = (name, function, dependencies, run_kwargs)
            assert name not in self.tasks
            self.tasks[name] = task
            return Result(task)

        return wrapper


def collect(workflow_function, folder):
    collector = Collector()
    try:
        workflow_function(collector.collect)
    except StopCollecting:
        pass

    tasks = []
    for name, deps, kwargs in collector.tasks.values():
        command = WorkflowTask(workflow_function.path, name)

        restart = kwargs.pop('restart', 0)
        diskspace = kwargs.pop('diskspace', 0)

        res = Resources.from_args_and_command(
            command=command,
            folder=folder, **kwargs)

        task = Task(command,
                    deps=list(deps),
                    resources=res,
                    workflow=True,
                    restart=restart,
                    diskspace=diskspace,
                    folder=folder)
        tasks.append(task)
    return tasks


class Runner:
    def __init__(self, name):
        self.name = name

    def wrap(self, function, name=None, **kwargs):
        name = name or get_name(function)

        if not hasattr(function, 'is_done'):
            function = Cached(function, name)

        def wrapper(*args, **kwargs):
            if name == self.name:
                function(*args, **kwargs)
                raise StopRunning
            if function.is_done(*args, **kwargs):
                return function(*args, **kwargs)
            return Result(None)

        return wrapper


if __name__ == '__main__':
    script, name = sys.argv[1:]
    workflow_function = get_workflow_function(Path(script))
    try:
        workflow_function(Runner(name).wrap)
    except StopRunning:
        pass
