from pathlib import Path
from typing import Callable, List, Dict, Any
import importlib.util
from importlib import import_module

from .task import Task
from .utils import chdir


def workflow(args, folders: List[Path]) -> List[Task]:
    alltasks: List[Task] = []

    if args.pattern:
        assert args.script
        for folder in folders:
            for path in folder.glob('**/*' + args.script):
                create_tasks = compile_create_tasks_function(path)

                alltasks += get_tasks_from_folder(path.parent, create_tasks)
    else:
        if args.script:
            create_tasks = compile_create_tasks_function(Path(args.script))
        else:
            assert args.module
            # Make create tasks from dependency tree
            create_tasks = create_tasks_from_module(Path(args.module))

        for folder in folders:
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
    script = path.read_text()
    code = compile(script, str(path), 'exec')
    namespace: Dict[str, Any] = {}
    exec(code, namespace)
    create_tasks = namespace['create_tasks']
    return create_tasks


def get_tasks_from_folder(folder: Path,
                          create_tasks: Callable[[], List[Task]]
                          ) -> List[Task]:
    tasks = []
    with chdir(folder):
        newtasks = create_tasks()
    for task in newtasks:
        if not task.skip():
            task.workflow = True
            tasks.append(task)
    return tasks


def create_tasks_from_module(path: Path) -> Callable[[], List[Task]]:
    # Initialize before running
    modules = {}
    get_relevant_modules(path, modules=modules)

    def create_tasks():
        tasks = []
        get_tasks(path, modules, tasks)
        tasks = tasks[::-1]
        return tasks

    return create_tasks


def get_relevant_modules(path: Path,
                         modules: Dict[str, Any] = {}):
    cmd = str(path)
    if cmd not in modules:
        module = get_module(path)
        modules[cmd] = module

        if hasattr(module, 'dependencies'):
            for dep in module.dependencies:
                get_relevant_modules(Path(dep), modules=modules)


def get_module(path: Path) -> Dict[str, Any]:
    if path.is_file():
        spec = importlib.util.spec_from_file_location('', str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = import_module(str(path))

    return module


def get_tasks(path: Path, modules: Dict[str, Any], tasks: List[Task]):
    # Is this recipe already in the tasks?
    cmd = str(path)
    if cmd in [task.cmd.name for task in tasks]:
        return
    module = modules[cmd]
    task = task_from_module(cmd, module)
    tasks.append(task)

    if hasattr(module, 'dependencies'):
        for dependency in module.dependencies:
            get_tasks(Path(dependency), modules, tasks)


def task_from_module(cmd: Path, module: Any):
    from myqueue.task import task

    attributes = ['resources', 'diskspace',
                  'dependencies', 'restart']
    kwargs = {}
    for attr in attributes:
        if hasattr(module, attr):
            var = getattr(module, attr)
            if callable(var):
                var = var()
            kwargs[attr] = var

    if 'dependencies' in kwargs:
        deps = kwargs.pop('dependencies')
        kwargs['deps'] = deps

    return task(cmd=str(cmd),
                **kwargs)
