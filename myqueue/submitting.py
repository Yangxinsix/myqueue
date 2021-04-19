import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Sequence
from graphlib import TopologicalSorter

from myqueue.progress import progress_bar
from myqueue.scheduler import Scheduler
from myqueue.task import Task
from myqueue.utils import plural
from myqueue.virtenv import find_activation_scripts

from .states import State


def submit_tasks(scheduler: Scheduler,
                 tasks: Sequence[Task],
                 current: Dict[Path, Task],
                 force: bool,
                 max_tasks: int,
                 verbosity: int,
                 dry_run: bool) -> Tuple[List[Task],
                                         List[Task],
                                         Optional[Exception]]:
    # See https://xkcd.com/1421

    tasks2 = []
    done = set()
    for task in tasks:
        if task.workflow and task.is_done():
            done.add(task.dname)
        else:
            tasks2.append(task)
    tasks = tasks2
    if done:
        print(plural(len(done), 'task'), 'already done')

    tasks2 = []
    failed_tasks = []
    for task in tasks:
        if task.workflow and task.has_failed():
            if force:
                if not dry_run:
                    task.remove_failed_file()
                tasks2.append(task)
            else:
                failed_tasks.append(task.dname)
        else:
            tasks2.append(task)
    nfailed = len(tasks) - len(tasks2)
    if nfailed:
        print(plural(nfailed, 'task'),
              'already marked as FAILED '
              '("<task-name>.FAILED" file exists).')
        print('Use --force to ignore and remove the .FAILED files.')
    tasks = tasks2

    tasks2 = []
    inqueue: Dict[State, int] = defaultdict(int)
    for task in tasks:
        if task.workflow and task.dname in current:
            state = current[task.dname].state
            if state in {'queued', 'hold', 'running'}:
                inqueue[state] += 1
            else:
                tasks2.append(task)
        else:
            tasks2.append(task)
    tasks = tasks2

    if inqueue:
        print(plural(sum(inqueue.values()), 'task'),
              'already in the queue:')
        print('\n'.join(f'    {state:8}: {n}'
                        for state, n in inqueue.items()))

    todo = []
    for task in tasks:
        task.dtasks = []
        for dep in task.deps:
            # convert dep to Task:
            if dep in failed_tasks:
                print(f'Skipping {task.dname}. '
                      f'Reason: Failed dependency={dep}.')
                break
            tsk = current.get(dep)
            if tsk is None:
                for tsk in tasks:
                    if dep == tsk.dname:
                        break
                else:
                    assert dep in done, (
                        f'Missing dependency for {task.name}:', dep)

                    tsk = None
            elif tsk.state == 'done':
                tsk = None
            elif tsk.state not in {'queued', 'hold', 'running'}:
                print(f'Dependency for {task.name} ({tsk.name}) '
                      f'in bad state: {tsk.state}')
                break

            if tsk is not None:
                task.dtasks.append(tsk)
        else:
            task.deps = [t.dname for t in task.dtasks]
            todo.append(task)

    # All dependensies must have an id or be in the list of tasks
    # about to be submitted
    todo = [task for task in todo
            if all(tsk.id or tsk in todo for tsk in task.dtasks)]

    todo = todo[:max_tasks]

    t = time.time()
    for task in todo:
        task.dtasks = [tsk for tsk in task.dtasks if not tsk.is_done()]
        task.state = State.queued
        task.tqueued = t

    activation_scripts = find_activation_scripts([task.folder
                                                  for task in todo])
    for task in todo:
        task.activation_script = activation_scripts.get(task.folder)

    sorter = TopologicalSorter({task: task.dtasks for task in todo})
    sorter.prepare()
    todo = []
    while sorter.is_active():
        for task in sorter.get_ready():
            if not any(dep.id == 0 for dep in task.dtasks):
                todo.append(task)
                sorter.done(task)

    pb = progress_bar(len(todo),
                      f'Submitting {len(todo)} tasks:',
                      verbosity and len(todo) > 1)
    submitted = []
    ex = None
    try:
        while todo:
            task = todo.pop(0)
            scheduler.submit(
                task,
                dry_run,
                verbosity >= 2)
            submitted.append(task)
            next(pb)
    except Exception as x:
        ex = x

    return submitted, todo, ex
