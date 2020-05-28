from pathlib import Path
from typing import Callable, List, Dict, Any

from .progress import show_progress
from .task import Task
from .utils import chdir, plural


def workflow(args, folders: List[Path], verbosity: int = 1) -> List[Task]:
    """Collect tasks from workflow script(s) and folders."""
    alltasks: List[Task] = []

    if args.pattern:
        paths = [path
                 for folder in folders
                 for path in folder.glob('**/*' + args.script)]
        for path in show_progress(paths,
                                  f'Scanning {len(paths)} scripts:',
                                  verbosity):
            create_tasks = compile_create_tasks_function(path)
            alltasks += get_tasks_from_folder(path.parent, create_tasks)
    else:
        assert args.script.endswith('.py'), args.script
        create_tasks = compile_create_tasks_function(Path(args.script))
        n_folders = plural(len(folders), 'folder')
        for folder in show_progress(folders,
                                    f'Scanning {n_folders}:',
                                    verbosity):
            alltasks += get_tasks_from_folder(folder, create_tasks)

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
