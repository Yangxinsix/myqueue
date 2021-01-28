import ast
import runpy
from pathlib import Path
from functools import partial
from typing import Callable, List, Dict, Any, Union, Set, Tuple

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
        tasks = workflow_from_script(Path(args.script),
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


WorkflowFunction = Callable[[Callable], None]


def get_workflow_function(path: Path, kwargs={}) -> WorkflowFunction:
    """Get workflow function from script."""
    module = runpy.run_path(str(path))  # type: ignore # bug in typeshed?
    try:
        func = module['workflow']
    except KeyError:
        func = module['create_tasks']
    if kwargs:
        name = func.__name__
        func = partial(func, **kwargs)
        func.__name__ = name
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
        tasks += get_tasks_from_folder(path.parent, func, path.absolute())
        next(pb)
    return tasks


def workflow_from_script(script: Path,
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
        tasks += get_tasks_from_folder(folder, func, script.absolute())
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
                          func: Callable,
                          script: Path) -> List[Task]:
    """Collect tasks from folder."""
    with chdir(folder):
        if func.__name__ == 'create_tasks':
            tasks = func()
        else:
            tasks = collect(func, folder, script)

    return tasks


class StopCollecting(Exception):
    """Workflow needs an actual result instead of a dummy Result object."""


class StopRunning(Exception):
    """The correct task has finished running: Stop workflow function."""


class Result:
    """Result object for a task - used for finding dependencies.

    >>> result = Result('task1')
    >>> x = result.data[42]
    >>> x is result
    True
    >>> x < 10
    Traceback (most recent call last):
        ...
    myqueue.workflow.StopCollecting
    """
    def __init__(self, name: str):
        self.name = name

    def __getitem__(self, key) -> 'Result':
        return self

    def __getattr__(self, attr) -> 'Result':
        return self

    def __gt__(self, other):
        raise StopCollecting

    __lt__ = __gt__


def get_name(func: Callable) -> str:
    """Give a name to a function.

    >>> import time
    >>> get_name(time.sleep)
    'time.sleep'
    """
    mod = func.__module__
    if mod in ['<run_path>', '__main__']:
        return func.__name__
    return f'{mod}.{func.__name__}'


def run(function: Callable,
        *,
        name: str = '',
        **kwargs) -> Callable:
    """Wrapper for just running the function."""
    return cached_function(function, name or get_name(function))


class Cached:
    """A caching function."""
    def __init__(self, function: Callable, name: str):
        self.function = function
        self.path = Path(f'{name}.done')

    def has(self, *args, **kwargs) -> bool:
        """Check if function has been called."""
        return self.path.is_file()

    def __call__(self, *args, **kwargs):
        if self.has():
            return eval(self.path.read_text())
        result = self.function(*args, **kwargs)
        self.path.write_text(repr(result))
        return result


def cached_function(function: Callable, name: str) -> Cached:
    """Wrap function if needed."""
    if hasattr(function, 'has'):
        return function  # type: ignore
    return Cached(function, name)


class Collector:
    """Wrapper for collecting tasks from workflow function."""
    def __init__(self):
        self.tasks: Dict[str, Tuple[Set[str], Dict[str, Any]]] = {}

    def collect(self,
                function: Union[Callable, Cached],
                *,
                name: str = '',
                deps: List[Result] = None,
                **run_kwargs) -> Callable:
        name = name or get_name(function)

        cfunction = cached_function(function, name)

        def wrapper(*args, **kwargs) -> Result:
            if cfunction.has(*args, **kwargs):
                return cfunction(*args, **kwargs)

            dependencies = set()
            for dep in list(args) + list(kwargs.values()) + (deps or []):
                if isinstance(dep, Result):
                    dependencies.add(dep.name)

            task = (dependencies, run_kwargs)
            assert name not in self.tasks
            self.tasks[name] = task
            return Result(name)

        return wrapper


def collect(workflow_function: Callable,
            folder: Path,
            script: Path) -> List[Task]:
    """Collecting tasks from workflow function."""
    collector = Collector()
    try:
        workflow_function(collector.collect)
    except StopCollecting:
        pass

    tasks = []
    for name, (deps, kwargs) in collector.tasks.items():
        command = WorkflowTask(f'{script}:{name}', [])

        restart = kwargs.pop('restart', 0)
        diskspace = kwargs.pop('diskspace', 0)

        res = Resources.from_args_and_command(
            command=command,
            path=folder, **kwargs)

        task = Task(command,
                    deps=[folder / dep for dep in deps],
                    resources=res,
                    workflow=True,
                    restart=restart,
                    diskspace=diskspace,
                    folder=folder,
                    creates=[])
        tasks.append(task)

    return tasks


class Runner:
    """Wrapper for running specific task in workflow function."""
    def __init__(self, name: str):
        self.name = name

    def wrap(self, function: Callable, name: str = '', **kwargs):
        name = name or get_name(function)

        cfunction = cached_function(function, name)

        def wrapper(*args, **kwargs):
            if name == self.name:
                cfunction(*args, **kwargs)
                raise StopRunning
            if cfunction.has(*args, **kwargs):
                return cfunction(*args, **kwargs)
            return Result('')

        return wrapper


def run_workflow_function(script: Path, name: str) -> None:
    """Run specific task in workflow function."""
    workflow_function = get_workflow_function(script)
    try:
        workflow_function(Runner(name).wrap)
    except StopRunning:
        pass


if __name__ == '__main__':
    # Used by WorkflowTask
    import sys
    script, name = sys.argv[1:]
    run_workflow_function(Path(script), name)
