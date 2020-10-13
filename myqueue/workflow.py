import ast
from pathlib import Path
from typing import Callable, List, Dict, Any, Union

from .progress import progress_bar
from .task import Task
from .utils import chdir, plural


def workflow(args, folders: List[Path], verbosity: int = 1) -> List[Task]:
    """Collect tasks from workflow script(s) and folders."""
    alltasks: List[Task] = []

    if args.pattern:
        paths = [path
                 for folder in folders
                 for path in folder.glob('**/*' + args.script)]
        pb = progress_bar(len(paths),
                          f'Scanning {len(paths)} scripts:',
                          verbosity)

        for path in paths:
            create_tasks = compile_create_tasks_function(path)
            alltasks += get_tasks_from_folder(path.parent, create_tasks)
            next(pb)
    else:
        assert args.script.endswith('.py'), args.script
        create_tasks = compile_create_tasks_function(Path(args.script))

        if args.arguments:
            kwargs = str2kwargs(args.arguments)
            old = create_tasks

            def create_tasks():
                return old(**kwargs)

        n_folders = plural(len(folders), 'folder')
        pb = progress_bar(len(folders),
                          f'Scanning {n_folders}:',
                          verbosity)
        for folder in folders:
            alltasks += get_tasks_from_folder(folder, create_tasks)
            next(pb)

    if args.targets:
        names = args.targets.split(',')
        include = set()
        map = {task.dname: task for task in alltasks}
        for task in alltasks:
            if task.cmd.name in names:
                for t in task.ideps(map):
                    include.add(task)
        alltasks = list(include)

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


def compile_create_tasks_function(path: Path) -> Callable[[], List[Task]]:
    """Compile create_tasks() function from worflow Python script."""
    script = path.read_text()
    code = compile(script, str(path), 'exec')
    namespace: Dict[str, Any] = {}
    exec(code, namespace)
    create_tasks = namespace['create_tasks']
    return create_tasks


def get_tasks_from_folder(folder: Path,
                          create_tasks: Callable[[], List[Task]]
                          ) -> List[Task]:
    """Collect tasks from folder."""
    tasks = []
    with chdir(folder):
        newtasks = create_tasks()
    for task in newtasks:
        if not task.skip():
            task.workflow = True
            tasks.append(task)
    return tasks
