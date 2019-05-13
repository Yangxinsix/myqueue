import argparse
import sys
import textwrap
from pathlib import Path
from typing import List, Any, Tuple, Dict, Set, Optional


class MQError(Exception):
    """For nice (expected) CLI errors."""


main_description = """\
Simple frontend for SLURM/PBS.

Type "mq help <command>" for help.
See https://myqueue.readthedocs.io/ for more information.
"""

_help = """\
help
Show how to use this tool.
More help can be found here: https://myqueue.readthedocs.io/.
.
list
List tasks in queue.
Only tasks in the chosen folder and its subfolders are shown.

Examples:

    $ mq list -s rq  # show running and queued jobs
    $ mq ls -s F abc/  # show failed jobs in abc/ folder
.
submit
Submit task(s) to queue.
Example:

    $ mq submit script.py -R 24:1d  # 24 cores for 1 day
.
resubmit
Resubmit failed or timed-out tasks.
Example:

    $ mq resubmit -i 4321  # resubmit job with id=4321
.
remove
Remove or cancel task(s).
Examples:

    $ mq remove -i 4321,4322  # remove jobs with ids 4321 and 4322
    $ mq rm -s d . -r  # remove done jobs in this folder and its subfolders
.
workflow
Submit tasks from script.
The script can be a simple Python script or a Python
module. If script/module contains a create_tasks() function then create
tasks defined in this function. Otherwise look for "dependencies" and
"resources" variables in script and create workflow tree from these variables.
Example of script containing "create_tasks()":

    $ cat flow.py
    from myqueue.task import task
    def create_tasks():
        return [task('task1'),
                task('task2', deps='task1')]
    $ mq workflow flow.py F1/ F2/  # submit tasks in F1 and F2 folders

Myqueue can also deduce a workflow from a script itself by looking for the
resources and dependencies variables. For example, to tell myqueue that script
"a.py" depends on "b.py" then "a.py" must contain:

    $ cat a.py
    ...
    dependencies = ['b.py']
    ...

Similarly, resources can be given by specifying "resources = '8:10h'"
which would give 8 cores for 10 hours.
.
kick
Restart T and M tasks (timed-out and out-of-memory).
You can kick the queue manually with "mq kick" or automatically by adding that
command to a crontab job (can be done with "mq kick --install-crontab-job").
.
completion
Set up tab-completion for Bash.
Do this:

    $ mq completion >> ~/.bashrc
.
test
Run tests.
Please report errors to https://gitlab.com/jensj/myqueue/issues.

.
modify
Modify task(s).
The following state changes are allowed: h->q, q->h, F->M and F->T.
.
init
Initialize new queue.
This will create a .myqueue/ folder in your current working directory
and copy ~/.myqueue/config.py into it.
.
info
Show detailed information about task.

.
sync
Make sure SLURM/PBS and MyQueue are in sync.
Remove tasks that SLURM/PBS doesn't know about.  Also removes a task
if its corresponding folder no longer exists.
"""

submit_usage = """\
mq submit [-h] [-d DEPENDENCIES] [-n NAME] [--restart N] [-R RESOURCES]
                 [-w] [-z] [-v] [-q] [-T]
                 task [folder [folder ...]]
                 [-- arg [arg ...]]
"""

aliases = {'rm': 'remove',
           'ls': 'list'}


commands: Dict[str, Tuple[str, str]] = {}
for lines in _help.split('\n.\n'):
    cmd, help, description = lines.split('\n', 2)
    if description:
        description = help + '\n\n' + description
    else:
        description = help
    commands[cmd] = (help, description)


def main(arguments: List[str] = None) -> Any:
    parser = argparse.ArgumentParser(
        prog='mq',
        formatter_class=Formatter,
        description=main_description)

    subparsers = parser.add_subparsers(title='Commands', dest='command')

    for cmd, (help, description) in commands.items():
        p = subparsers.add_parser(cmd,
                                  description=description,
                                  help=help,
                                  usage=(submit_usage if cmd == 'submit'
                                         else None),
                                  formatter_class=Formatter,
                                  aliases=[alias for alias in aliases
                                           if aliases[alias] == cmd])
        a = p.add_argument

        if cmd == 'help':
            a('cmd', nargs='?', help='Subcommand.')
            continue

        if cmd == 'test':
            a('test', nargs='*',
              help='Test to run.  Default behaviour is to run all.')
            a('--config-file',
              help='Use specific config.py file.')
            a('-x', '--exclude',
              help='Exclude test(s).')

        elif cmd == 'submit':
            a('task', help='Task to submit.')
            a('-d', '--dependencies', default='',
              help='Comma-separated task names.')
            a('-n', '--name', help='Name used for task.')
            a('--restart', type=int, default=0, metavar='N',
              help='Restart N times if task times out or runs out of memory. '
              'Time-limit will be doubled for a timed out task and '
              'number of cores will be increased to the next number of nodes '
              'for a task that runs out of memory.')
            a('folder',
              nargs='*', default=['.'],
              help='Submit tasks in this folder.  '
              'Defaults to current folder.')

        if cmd in ['resubmit', 'submit']:
            a('-R', '--resources',
              help='Examples: "8:1h", 8 cores for 1 hour. '
              'Use "m" for minutes, '
              '"h" for hours and "d" for days. '
              '"16:1:30m": 16 cores, 1 process, half an hour.')
            a('-w', '--workflow', action='store_true',
              help='Write <task-name>.done or <task-name>.FAILED file '
              'when done.')

        if cmd == 'modify':
            a('newstate', help='New state (one of the letters: qhrdFCTM).')

        if cmd == 'workflow':
            help = ('Workflow submit script or module. If module, then create '
                    'workflow from module dependencies')
            a('script', help=help,
              default=None)
            a('-t', '--targets',
              help='Comma-separated target names.  Without any targets, '
              'all tasks will be submitted.')
            a('-p', '--pattern', action='store_true',
              help='Use submit scripts matching "pattern" in all '
              'subfolders.')
            a('folder',
              nargs='*', default=['.'],
              help='Submit tasks in this folder.  '
              'Defaults to current folder.')

        if cmd in ['list', 'remove', 'resubmit', 'modify']:
            a('-s', '--states', metavar='qhrdFCTM',
              help='Selection of states. First letters of "queued", "hold", '
              '"running", "done", "FAILED", "CANCELED" and "TIMEOUT".')
            a('-i', '--id', help="Comma-separated list of task ID's. "
              'Use "-i -" for reading ID\'s from stdin '
              '(one ID per line; extra stuff after the ID will be ignored).')
            a('-n', '--name',
              help='Select only tasks named "NAME".')

        if cmd == 'list':
            a('-c', '--columns', metavar='ifnraste', default='ifnraste',
              help='Select columns to show.')
            a('-S', '--sort', metavar='c',
              help='Sort rows using column c, where c must be one of '
              'i, f, n, r, a, s, t or e.  Use "-S c-" for a descending sort.')

        if cmd not in ['list', 'completion']:
            a('-z', '--dry-run',
              action='store_true',
              help='Show what will happen without doing anything.')

        a('-v', '--verbose', action='count', default=0, help='More output.')
        a('-q', '--quiet', action='count', default=0, help='Less output.')
        a('-T', '--traceback', action='store_true',
          help='Show full traceback.')

        if cmd in ['remove', 'resubmit', 'modify']:
            a('-r', '--recursive', action='store_true',
              help='Use also subfolders.')
            a('folder',
              nargs='*',
              help='Task-folder.  Use --recursive (or -r) to include '
              'subfolders.')

        if cmd in ['list', 'sync', 'kick']:
            a('-A', '--all', action='store_true',
              help=f'{cmd.title()} all myqueue folders '
              '(from ~/.myqueue/folders.txt)')
            a('folder',
              nargs='?',
              help=f'{cmd.title()} tasks in this folder and its subfolders.  '
              'Defaults to current folder.')

        if cmd == 'kick':
            a('--install-crontab-job', action='store_true',
              help='Install crontab job to kick your queues every half hour.')

        if cmd == 'info':
            a('id', type=int, help='Task ID.')
            a('folder',
              nargs='?',
              help='Show task from this folder.  Defaults to current folder.')

    # Extract extra argument for task:
    args1 = arguments or sys.argv[1:]
    try:
        i = args1.index('--')
    except ValueError:
        extra: List[str] = []
    else:
        extra = args1[i + 1:]
        del args1[i:]

    args = parser.parse_args(args1)

    args.command = aliases.get(args.command, args.command)

    # Create ~/.myqueue/ if it's not there:
    f = Path.home() / '.myqueue'
    if not f.is_dir():
        f.mkdir()

    if args.command is None:
        parser.print_help()
        print('\nCode:', Path(__file__).parent)
        return

    if args.command == 'help':
        if args.cmd is None:
            parser.print_help()
        else:
            subparsers.choices[args.cmd].print_help()  # type: ignore
        return

    if args.command == 'test':
        from myqueue.test.tests import run_tests
        exclude = args.exclude.split(',') if args.exclude else []
        config = Path(args.config_file) if args.config_file else None
        run_tests(args.test, config, exclude, args.verbose)
        return

    if args.command == 'completion':
        cmd = ('complete -o default -C "{py} {filename}" mq'
               .format(py=sys.executable,
                       filename=Path(__file__).with_name('complete.py')))
        if args.verbose:
            print('Add tab-completion for Bash by copying the following '
                  'line to your ~/.bashrc (or similar file):\n\n   {cmd}\n'
                  .format(cmd=cmd))
        else:
            print(cmd)
        return

    try:
        results = run(args, extra)
        if arguments:
            return results
    except KeyboardInterrupt:
        pass
    except MQError as x:
        parser.exit(1, str(x) + '\n')
    except Exception as x:
        if args.traceback:
            raise
        else:
            print('{}: {}'.format(x.__class__.__name__, x),
                  file=sys.stderr)
            print('To get a full traceback, use: mq {} ... -T'
                  .format(args.command), file=sys.stderr)
            return 1


def run(args: argparse.Namespace, extra: List[str]):
    from .config import config, initialize_config
    from .resources import Resources
    from .task import task, Task, taskstates
    from .runner import Runner, Selection, pprint
    from .utils import get_home_folders
    from .workflow import workflow

    verbosity = 1 - args.quiet + args.verbose

    if args.command == 'init':
        folders = get_home_folders()
        root = Path.cwd()
        if root in folders:
            raise MQError(
                f'The folder {root} has already been initialized!')
        mq = root / '.myqueue'
        mq.mkdir()
        path = Path.home() / '.myqueue'
        cfg = path / 'config.py'
        if cfg.is_file():
            (mq / 'config.py').write_text(cfg.read_text())

        folders.append(root)
        (path / 'folders.txt').write_text('\n'.join(str(folder)
                                                    for folder in folders) +
                                          '\n')
        return

    if args.command == 'kick' and args.install_crontab_job:
        from myqueue.crontab import install_crontab_job
        install_crontab_job(args.dry_run)
        return

    folder_names: List[str] = []
    if args.command in ['list', 'sync', 'kick', 'info']:
        if args.command != 'info' and args.all:
            if args.folder is not None:
                raise MQError('Specifying a folder together with --all '
                              'does not make sense')
        else:
            folder_names = [args.folder or '.']
    else:
        folder_names = args.folder

    folders = [Path(folder).expanduser().absolute().resolve()
               for folder in folder_names]

    if args.command != 'submit' and extra:
        raise MQError('No extra arguments allowed')

    if args.command in ['remove', 'resubmit', 'modify']:
        if not folders:
            if args.id:
                folders = [Path.cwd()]
            else:
                raise MQError('Missing folder!')

    if folders:
        start = folders[0]
        try:
            initialize_config(start)
        except ValueError:
            raise MQError(
                f'The folder {start} is not inside a MyQueue tree.\n'
                'You can create a tree with "cd <root-of-tree>; mq init".')

        home = config['home']
        if verbosity > 1:
            print('Root:', home)
        for folder in folders[1:]:
            try:
                folder.relative_to(home)
            except ValueError:
                raise MQError('{folder} not inside {home}'
                              .format(folder=folder, home=home))

    if args.command in ['list', 'remove', 'resubmit', 'modify']:
        default = 'qhrdFCTM' if args.command == 'list' else ''
        states = set()
        for s in args.states if args.states is not None else default:
            for state in taskstates:
                if s == state[0]:
                    states.add(state)
                    break
            else:
                raise MQError('Unknown state: ' + s)

        ids: Optional[Set[int]] = None
        if args.id:
            if args.states is not None:
                raise MQError("You can't use both -i and -s!")
            if args.folder:
                raise ValueError("You can't use both -i and folder(s)!")

            if args.id == '-':
                ids = {int(line.split()[0]) for line in sys.stdin}
            else:
                ids = {int(id) for id in args.id.split(',')}
        elif args.command != 'list' and args.states is None:
            raise MQError('You must use "-i <id>" OR "-s <state(s)>"!')

        selection = Selection(ids, args.name, states,
                              folders, getattr(args, 'recursive', True))

    if args.command == 'list' and args.all:
        folders = get_home_folders()
        selection.folders = folders
        alltasks: List[Task] = []
        for folder in folders:
            initialize_config(folder, force=True)
            with Runner(verbosity) as runner:
                runner.tasks = alltasks
                runner._read()
        if alltasks:
            alltasks = runner.select(selection)
            pprint(alltasks, verbosity, args.columns)
        return

    if args.command in ['sync', 'kick'] and args.all:
        for folder in get_home_folders():
            initialize_config(folder, force=True)
            with Runner(verbosity) as runner:
                if args.command == 'sync':
                    runner.sync(args.dry_run)
                else:
                    runner.kick(args.dry_run)
        return

    with Runner(verbosity, need_lock=args.command != 'list') as runner:
        if args.command == 'list':
            if args.sort:
                reverse = args.sort.endswith('-')
                column = args.sort.rstrip('-')
            else:
                reverse = False
                column = None
            return runner.list(selection, args.columns, column, reverse)

        if args.command == 'remove':
            runner.remove(selection, args.dry_run)

        elif args.command == 'resubmit':
            if args.resources:
                resources = Resources.from_string(args.resources)
            else:
                resources = None
            runner.resubmit(selection, args.dry_run, resources)

        elif args.command == 'submit':
            newtasks = [task(args.task,
                             args=extra,
                             resources=args.resources,
                             name=args.name,
                             folder=str(folder),
                             deps=args.dependencies,
                             workflow=args.workflow,
                             restart=args.restart)
                        for folder in folders]

            runner.submit(newtasks, args.dry_run)

        elif args.command == 'modify':
            runner.modify(selection, args.newstate, args.dry_run)

        elif args.command == 'workflow':
            tasks = workflow(args, folders)
            runner.submit(tasks, args.dry_run)

        elif args.command == 'sync':
            runner.sync(args.dry_run)

        elif args.command == 'kick':
            runner.kick(args.dry_run)

        elif args.command == 'info':
            runner.info(args.id)

        else:
            assert False


class Formatter(argparse.HelpFormatter):
    """Improved help formatter."""
    def _fill_text(self, text, width, indent):
        assert indent == ''
        out = ''
        blocks = text.split('\n\n')
        for block in blocks:
            if block[0] == '*':
                # List items:
                for item in block[2:].split('\n* '):
                    out += textwrap.fill(item,
                                         width=width - 2,
                                         initial_indent='* ',
                                         subsequent_indent='  ') + '\n'
            elif block[0] == ' ':
                # Indented literal block:
                out += block + '\n'
            else:
                # Block of text:
                out += textwrap.fill(block, width=width) + '\n'
            out += '\n'
        return out[:-1]
