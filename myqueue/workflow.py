import ast
import runpy
from pathlib import Path
from typing import Callable, List, Dict, Any, Union

from .progress import progress_bar
from .task import Task, task as create_task
from .utils import chdir, plural


DEFAULT_VERBOSITY = 1


def workflow_from_function(
        workflow_function: Callable[..., List[Task]],
        folders: List[Path],
        verbosity: int = DEFAULT_VERBOSITY) -> List[Task]:
    """Collect tasks from workflow defined in python script."""
    alltasks: List[Task] = []

    n_folders = plural(len(folders), 'folder')
    pb = progress_bar(len(folders),
                      f'Scanning {n_folders}:',
                      verbosity)
    for folder in folders:
        alltasks += get_tasks_from_folder(folder, workflow_function)
        next(pb)

    return alltasks


def workflow_from_pattern(
        script: str,
        folders: List[Path],
        verbosity: int = DEFAULT_VERBOSITY) -> List[Task]:
    """Generate tasks from workflows defined by '**/*{script}'."""
    alltasks: List[Task] = []
    paths = [path
             for folder in folders
             for path in folder.glob('**/*' + script)]
    pb = progress_bar(len(paths),
                      f'Scanning {len(paths)} scripts:',
                      verbosity)

    for path in paths:
        create_tasks = compile_create_tasks_function(path)
        alltasks += get_tasks_from_folder(path.parent, create_tasks)
        next(pb)
    return alltasks


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


def workflow(args,
             folders: List[Path],
             verbosity: int = DEFAULT_VERBOSITY) -> List[Task]:
    """Collect tasks from workflow script(s) and folders."""
    if args.pattern:
        alltasks = workflow_from_pattern(
            script=args.script,
            folders=folders,
            verbosity=verbosity)
    else:
        assert args.script.endswith('.py'), args.script
        create_tasks = compile_create_tasks_function(Path(args.script))

        if args.arguments:
            kwargs = str2kwargs(args.arguments)
            old = create_tasks

            def create_tasks():
                return old(**kwargs)

        alltasks = workflow_from_function(
            workflow_function=create_tasks,
            folders=folders,
            verbosity=verbosity)

    if args.targets:
        names = args.targets.split(',')
        alltasks = filter_tasks(tasks=alltasks, names=names)

    return alltasks


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


def compile_create_tasks_function(path: Path) -> Callable[..., List[Task]]:
    """Compile create_tasks() function from worflow Python script."""
    script = path.read_text()
    code = compile(script, str(path), 'exec')
    namespace: Dict[str, Any] = {}
    exec(code, namespace)
    create_tasks = namespace.get('workflow', namespace['create_tasks'])
    return create_tasks


def get_tasks_from_folder(folder: Path,
                          create_tasks: Callable[[], List[Task]]
                          ) -> List[Task]:
    """Collect tasks from folder."""
    with chdir(folder):
        newtasks = create_tasks()
    tasks = []
    for task in newtasks:
        if not task.skip():
            task.workflow = True
            tasks.append(task)
    return tasks


def get_tasks_from_folder_new(folder: Path,
                              workflow: Callable[[Callable], None]
                              ) -> List[Task]:
    """Collect tasks from folder."""
    with chdir(folder):
        run = Collector()
        workflow(run)
    tasks = []
    for task in run.tasks:
        if not task.skip():
            task.workflow = True
            tasks.append(task)
    return tasks


class Collector:
    def __init__(self, target=None):
        self.tasks
        self.target = target

    def __call__(self, func, *args, **kwargs):

        mqkwargs = {}
        for key in ['name', 'resources', 'tmax']:
            if key in kwargs:
                mqkwargs[key] = kwargs.pop(key)

        name = mqkwargs.pop('name')
        if name is None:
            name = get_name(func, args, kwargs)

        if self.target:
            result = func(*args, **kwargs)
            if self.target == name:
                self.target = None
                return result

        assert name not in self.tasks

        args = list(args) + list(kwargs.values())
        deps = set()
        for arg in args:
            if isinstance(arg, Result):
                deps.add(arg.task)

        task = create_task('workflow:script_path',
                           args=[name],
                           deps=list(deps),
                           name=name,
                           **mqkwargs)
        self.tasks[name] = task

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


def run(path, target: str) -> None:
    module = runpy.run_path(path)
    run = Collector(target)
    module.workflow(run)
    