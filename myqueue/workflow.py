import ast
import runpy
from pathlib import Path
from functools import partial
from typing import Callable, List, Dict, Any, Union, Optional

from .progress import progress_bar
from .task import Task, UNSPECIFIED
from .utils import chdir, plural
from myqueue.commands import WorkflowTask, PythonModule, Command
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


WorkflowFunction = Callable[[], None]


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


class RunHandle:
    """Result of calling run().  Can be used as a context manager."""
    def __init__(self, task, runner):
        self.task = task
        self.runner = runner
        self._result = UNSPECIFIED

    @property
    def result(self):
        """Result from Python-function tasks."""
        result = self.task.result
        if result is UNSPECIFIED:
            return Result(self.task)
        return result

    def __enter__(self):
        self.runner.dependencies.append(self.task)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        task = self.runner.dependencies.pop()
        assert task is self.task


class Result:
    """Result object for a task - used for finding dependencies."""
    def __init__(self, task):
        self.task = task

    def __getattr__(self, attr) -> 'Result':
        return self

    def __lt__(self, other):
        raise StopCollecting

    __gt__ = __lt__

    __getitem__ = __getattr__
    __add__ = __getattr__


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


class Cached:
    """A caching function."""
    def __init__(self, function: Callable, name: str):
        self.function = function
        self.path = Path(f'{name}.done')

    def has(self, *args, **kwargs) -> bool:
        """Check if function has been called."""
        return self.path.is_file()

    def __call__(self):
        if self.has():
            return eval(self.path.read_text())
        result = self.function()
        self.path.write_text(repr(result))
        return result


def cached_function(function: Callable, name: str) -> Cached:
    """Wrap function if needed."""
    if hasattr(function, 'has'):
        return function  # type: ignore
    return Cached(function, name)


class ResourceHandler:
    """Resource decorator and context manager."""
    def __init__(self, kwargs, runner):
        self.kwargs = kwargs
        self.runner = runner
        self.old_kwargs: Dict

    def __call__(self, workflow_function):
        def new():
            with self:
                return workflow_function()
        return new

    def __enter__(self):
        self.old_kwargs = self.runner.resource_kwargs
        self.runner.resource_kwargs = {**self.old_kwargs, **self.kwargs}

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.runner.resource_kwargs = self.old_kwargs


class Runner:
    """Wrapper for collecting tasks from workflow function."""
    def __init__(self):
        self.tasks: Optional[List[Task]] = None
        self.dependencies: List[Task] = []
        self.resource_kwargs = {'tmax': '10m',
                                'cores': 1,
                                'nodename': '',
                                'processes': 0,
                                'restart': 0}
        self.target = ''
        self.workflow_script: Optional[Path] = None

    def run(self,
            *,
            function: Union[Callable, Cached] = None,
            script: Union[Path, str] = None,
            module: str = None,
            name: str = '',
            args=[],
            kwargs={},
            deps: List[RunHandle] = [],
            tmax: str = None,
            cores: int = None,
            nodename: str = None,
            processes: int = None,
            restart: int = None,
            folder: Union[Path, str] = '.') -> RunHandle:
        """Run or submit a task.
        """
        dependencies = self.extract_dependencies(args, kwargs, deps)

        resource_kwargs = {}
        values = [tmax, cores, nodename, processes, restart]
        for value, (key, default) in zip(values,
                                         self.resource_kwargs.items()):
            resource_kwargs[key] = value if value is not None else default

        task = create_task(function,
                           script,
                           module,
                           name,
                           args,
                           kwargs,
                           dependencies,
                           self.workflow_script,
                           Path(folder).absolute(),
                           resource_kwargs.pop('restart'),  # type: ignore
                           **resource_kwargs)

        if self.target:
            if task.cmd.fname == self.target:
                task.run()
                raise StopRunning
        elif self.tasks is not None:
            self.tasks.append(task)
        else:
            task.run()

        return RunHandle(task, self)

    def extract_dependencies(self,
                             args: List[Any],
                             kwargs: Dict[str, Any],
                             deps: List[RunHandle]) -> List[Path]:
        """Find dependencies on other tasks."""
        tasks = set(self.dependencies)
        for handle in deps:
            tasks.add(handle.task)
        for thing in list(args) + list(kwargs.values()):
            if isinstance(thing, Result):
                tasks.add(thing.task)
        return [task.dname for task in tasks]

    def wrap(self, function: Callable, **run_kwargs) -> Callable:
        """Wrap a function as a task.

        These two are equivalent::

            result = run(function=func, args=args, kwargs=kwargs, ...).result
            result = wrap(func, ...)(*args, **kwargs, ...)

        """
        def wrapper(*args, **kwargs):
            handle = self.run(function=function,
                              args=args,
                              kwargs=kwargs,
                              **run_kwargs)
            return handle.result
        return wrapper

    def resources(self,
                  *,
                  tmax: str = None,
                  cores: int = None,
                  nodename: str = None,
                  processes: int = None,
                  restart: int = None) -> ResourceHandler:
        """Resource decorator and context manager."""
        keys = ['tmax', 'cores', 'nodename', 'processes', 'restart']
        values = [tmax, cores, nodename, processes, restart]
        kwargs = {key: value
                  for key, value in zip(keys, values)
                  if value is not None}
        return ResourceHandler(kwargs, self)


def create_task(function: Callable = None,
                script: Union[Path, str] = None,
                module: str = None,
                name: str = '',
                args: List[Any] = [],
                kwargs: Dict[str, Any] = {},
                deps: List[Path] = [],
                workflow_script: Path = None,
                folder: Path = Path('.'),
                restart: int = 0,
                **resource_kwargs) -> Task:
    """Create a Task object."""
    workflow = True
    command: Command

    if function:
        name = name or get_name(function)
        function = partial(function, *args, **kwargs)
        cfunction = cached_function(function, name)
        command = WorkflowTask(f'{workflow_script}:{name}', [], cfunction)
        workflow = False
    elif module:
        assert not kwargs
        command = PythonModule(module, [str(arg) for arg in args])

    res = Resources.from_args_and_command(command=command,
                                          path=folder,
                                          **resource_kwargs)

    task = Task(command,
                deps=deps,
                resources=res,
                workflow=workflow,
                folder=folder,
                restart=restart,
                diskspace=0,
                creates=[])

    if function and cfunction.has(*args, **kwargs):
        task.result = cfunction()
        task._done = True

    return task


runner = Runner()
run = runner.run
wrap = runner.wrap
resources = runner.resources


def collect(workflow_function: Callable,
            folder: Path,
            script: Path) -> List[Task]:
    """Collecting tasks from workflow function."""
    runner.tasks = []
    runner.workflow_script = script
    try:
        workflow_function()
    except StopCollecting:
        pass

    tasks = runner.tasks
    runner.tasks = None
    return tasks


def run_workflow_function(script: Path, name: str) -> None:
    """Run specific task in workflow function."""
    workflow_function = get_workflow_function(script)
    runner.target = name
    try:
        workflow_function()
    except StopRunning:
        pass
    runner.target = ''
