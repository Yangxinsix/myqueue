import argparse
import re
import sys
import textwrap
from pathlib import Path
from typing import List, Any, Tuple, Dict, Set, Optional, Pattern


class MQError(Exception):
    """For nice (expected) CLI errors."""


main_description = """\
Frontend for SLURM/PBS.

Type "mq help <command>" for help.
See https://myqueue.readthedocs.io/ for more information.
"""

_help = [
    ('help',
     'Show how to use this tool.', """
More help can be found here: https://myqueue.readthedocs.io/.
"""),
    ('list',
     'List tasks in queue.', """
Only tasks in the chosen folder and its subfolders are shown.

Examples:

    $ mq list -s rq  # show running and queued jobs
    $ mq ls -s F abc/  # show failed jobs in abc/ folder
"""),
    ('submit',
     'Submit task(s) to queue.', """
Example:

    $ mq submit script.py -R 24:1d  # 24 cores for 1 day
"""),
    ('resubmit',
     'Resubmit failed or timed-out tasks.', """
Example:

    $ mq resubmit -i 4321  # resubmit job with id=4321
"""),
    ('remove',
     'Remove or cancel task(s).', """
Examples:

    $ mq remove -i 4321,4322  # remove jobs with ids 4321 and 4322
    $ mq rm -s d . -r  # remove done jobs in this folder and its subfolders
"""),
    ('info',
     'Show detailed information about task.', """
Example:

    $ mq info 12345
"""),
    ('workflow',
     'Submit tasks from script.', """
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
"""),
    ('run',
     'Run task(s) on local computer.', """
Remove task(s) from queue and run locally.

Example:

    $ mq run script.py f1/ f2/
"""),
    ('kick',
     'Restart T and M tasks (timed-out and out-of-memory).', """
The queue is kicked automatically every ten minutes - so you don't have
to do it manually.
"""),
    ('modify',
     'Modify task(s).', """
The following state changes are allowed: h->q, q->h, F->M and F->T.
"""),
    ('init',
     'Initialize new queue.', """
This will create a .myqueue/ folder in your current working directory
and copy ~/.myqueue/config.py into it.
"""),
    ('sync',
     'Make sure SLURM/PBS and MyQueue are in sync.', """
Remove tasks that SLURM/PBS doesn't know about.  Also removes a task
if its corresponding folder no longer exists.
"""),
    ('completion',
     'Set up tab-completion for Bash.', """
Do this:

    $ mq completion >> ~/.bashrc
"""),
    ('test',
     'Run tests.', """
Please report errors to https://gitlab.com/myqueue/myqueue/issues.
""")]

aliases = {'rm': 'remove',
           'ls': 'list'}


commands: Dict[str, Tuple[str, str]] = {}
for cmd, help, description in _help:
    description = help + '\n\n' + description[1:]
    commands[cmd] = (help, description)


def main(arguments: List[str] = None) -> Any:
    parser = argparse.ArgumentParser(
        prog='mq',
        formatter_class=Formatter,
        description=main_description,
        allow_abbrev=False)

    subparsers = parser.add_subparsers(title='Commands', dest='command')

    short_options: Dict[str, int] = {}
    long_options: Dict[str, int] = {}

    for cmd, (help, description) in commands.items():
        p = subparsers.add_parser(cmd,
                                  description=description,
                                  help=help,
                                  formatter_class=Formatter,
                                  aliases=[alias for alias in aliases
                                           if aliases[alias] == cmd])

        def a(*args, **kwargs):
            """Wrapper for Parser.add_argument().

            Hack to fix argparse's handling of options.  See
            fix_option_order() function below."""

            x = p.add_argument(*args, **kwargs)
            if x is None:
                return
            for o in x.option_strings:
                nargs = x.nargs if x.nargs is not None else 1
                if o.startswith('--'):
                    long_options[o] = nargs
                else:
                    short_options[o[1]] = nargs

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
            a('-u', '--update-source-code', action='store_true',
              help='Update the command-line examples in the documentation.')

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

        elif cmd == 'run':
            a('task', help='Task to run locally.')
            a('-n', '--name', help='Name used for task.')
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

        if cmd in ['resubmit', 'submit', 'run']:
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
            a('-C', '--count', action='store_true',
              help='Just show the number of tasks.')

        if cmd not in ['list', 'completion', 'info', 'test']:
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

        if cmd == 'info':
            a('id', type=int, help='Task ID.')
            a('folder',
              nargs='?',
              help='Show task from this folder.  Defaults to current folder.')

    args = parser.parse_args(
        fix_option_order(arguments or sys.argv[1:],
                         short_options,
                         long_options))

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
            subparsers.choices[args.cmd].print_help()
        return

    if args.command == 'test':
        from myqueue.test.runner import run_tests
        exclude = args.exclude.split(',') if args.exclude else []
        config = Path(args.config_file) if args.config_file else None
        run_tests(args.test, config, exclude, args.verbose,
                  args.update_source_code)
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
        run(args)
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
            parser.exit(1)


def run(args: argparse.Namespace) -> None:
    from .config import config, initialize_config
    from .resources import Resources
    from .task import task, taskstates
    from .queue import Queue, Selection
    from .utils import get_home_folders
    from .workflow import workflow
    from .daemon import start_daemon

    start_daemon()

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

    for folder in folders:
        if not folder.is_dir():
            raise MQError('No such folder:', folder)

    if args.command in ['remove', 'resubmit', 'modify']:
        if not folders:
            if args.id:
                folders = [Path.cwd()]
            else:
                raise MQError('Missing folder!')

    if folders:
        # Find root folder:
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

        name: Optional[Pattern[str]]
        if args.name:
            name = re.compile(re.escape(args.name)
                              .replace('\\*', '.*')
                              .replace('\\?', '.'))
        else:
            name = None
        selection = Selection(ids, name, states,
                              folders, getattr(args, 'recursive', True))

    if args.command == 'list' and args.all:
        folders = get_home_folders()
        selection.folders = folders
        for folder in folders:
            initialize_config(folder, force=True)
            print(f'{folder}:')
            with Queue(verbosity, need_lock=False) as queue:
                if args.sort:
                    reverse = args.sort.endswith('-')
                    column = args.sort.rstrip('-')
                else:
                    reverse = False
                    column = None
                queue.list(selection, args.columns, column, reverse,
                           args.count)
        return

    if args.command in ['sync', 'kick'] and args.all:
        for folder in get_home_folders():
            initialize_config(folder, force=True)
            with Queue(verbosity, dry_run=args.dry_run) as queue:
                if args.command == 'sync':
                    queue.sync()
                else:
                    queue.kick()
        return

    need_lock = args.command not in ['list', 'info']
    dry_run = getattr(args, 'dry_run', False)
    with Queue(verbosity, need_lock, dry_run) as queue:
        if args.command == 'list':
            if args.sort:
                reverse = args.sort.endswith('-')
                column = args.sort.rstrip('-')
            else:
                reverse = False
                column = None
            queue.list(selection, args.columns, column, reverse, args.count)

        elif args.command == 'remove':
            queue.remove(selection)

        elif args.command == 'resubmit':
            resources: Optional[Resources]
            if args.resources:
                resources = Resources.from_string(args.resources)
            else:
                resources = None
            queue.resubmit(selection, resources)

        elif args.command == 'submit':
            newtasks = [task(args.task,
                             resources=args.resources,
                             name=args.name,
                             folder=str(folder),
                             deps=args.dependencies,
                             workflow=args.workflow,
                             restart=args.restart)
                        for folder in folders]

            queue.submit(newtasks)

        elif args.command == 'run':
            newtasks = [task(args.task,
                             name=args.name,
                             folder=str(folder),
                             workflow=args.workflow)
                        for folder in folders]
            queue.run(newtasks)

        elif args.command == 'modify':
            queue.modify(selection, args.newstate)

        elif args.command == 'workflow':
            tasks = workflow(args, folders)
            queue.submit(tasks)

        elif args.command == 'sync':
            queue.sync()

        elif args.command == 'kick':
            queue.kick()

        elif args.command == 'info':
            queue.info(args.id)

        else:
            assert False


class Formatter(argparse.HelpFormatter):
    """Improved help formatter."""
    # Bug in argparse types:
    # def _fill_text(self, text: str, width: int, indent: str) -> str:
    #     assert indent == ''
    def _fill_text(self, text: str, width: int, indent: int) -> str:
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


def fix_option_order(arguments: List[str],
                     short_options: Dict[str, int],
                     long_options: Dict[str, int]) -> List[str]:
    """Allow intermixed options and arguments."""
    args1: List[str] = []
    args2: List[str] = []
    i = 0
    while i < len(arguments):
        a = arguments[i]
        if a == '--':
            args2 += arguments[i:]
            break
        if a in long_options:
            n = long_options[a]
            args2 += arguments[i:i + 1 + n]
            i += n
        elif a.startswith('--') and '=' in a:
            args2.append(a)
        elif a.startswith('-'):
            for j, b in enumerate(a[1:]):
                n = short_options.get(b, 0)
                if n:
                    if j < len(a) - 2:
                        n = 0
                    args2 += arguments[i:i + 1 + n]
                    i += n
                    break
            else:
                args2.append(a)
        else:
            args1.append(a)
        i += 1
    return args1 + args2
