import argparse
import sys
from typing import List, Any


class MyQueueCLIError(Exception):
    pass


def main(arguments: List[str] = None) -> Any:
    parser = argparse.ArgumentParser(
        prog='mq',
        description='Simple frontend for SLURM.  '
        'Type "mq help <command>" for help.  '
        'See https://gitlab.com/jensj/myqueue for more information.')

    subparsers = parser.add_subparsers(title='Commands', dest='command')

    aliases = {'rm': 'delete',
               'ls': 'list'}

    for cmd, help in [('help', 'Show how to use this tool.'),
                      ('list', 'List tasks in queue.'),
                      ('submit', 'Submit task(s) to queue.'),
                      ('resubmit', 'Resubmit failed or timed-out tasks.'),
                      ('delete', 'Delete or cancel task(s).'),
                      ('workflow', 'Submit tasks from Python script.'),
                      ('completion', 'Set up tab-completion.'),
                      ('test', 'Run tests.')]:

        p = subparsers.add_parser(cmd, description=help, help=help,
                                  aliases=[alias for alias in aliases
                                           if aliases[alias] == cmd])
        a = p.add_argument

        if cmd == 'help':
            a('cmd', nargs='?')
            continue

        if cmd == 'test':
            a('test', nargs='*',
              help='Test to run.  Default behaviour is to run all.')
            a('--slurm', action='store_true',
              help='Run tests using SLURM.')

        elif cmd == 'submit':
            a('task', help='Task to submit.')
            a('-d', '--dependencies', default='',
              help='Comma-separated task names.')
            a('-a', '--arguments', help='Comma-separated arguments for task.')

        if cmd in ['resubmit', 'submit']:
            a('-R', '--resources',
              help='Examples: "8:1h", 8 cores for 1 hour. '
              'Use "m" for minutes, '
              '"h" for hours and "d" for days. '
              '"16:1:30m": 16 cores, 1 process, half an hour.')
            a('-w', '--workflow', action='store_true',
              help='Write <task-name>.done or <task-name>.FAILED file '
              'when done.')

        if cmd == 'workflow':
            a('script', help='Submit script.')
            a('-p', '--pattern', action='store_true',
              help='Use submit scripts matching "script" in all '
              'subfolders.')

        if cmd in ['list', 'delete', 'resubmit']:
            a('-s', '--states', metavar='qrdFCT',
              help='Selection of states. First letters of "queued", '
              '"running", "done", "FAILED", "CANCELED" and "TIMEOUT".')
            a('-i', '--id', help="Comma-separated list of task ID's.")
            a('-n', '--name',
              help='Select only tasks named "NAME".')

        if cmd == 'list':
            a('-c', '--columns', metavar='ifnraste', default='ifnraste',
              help='Select columns to show.')

        if cmd not in ['list', 'completion']:
            a('-z', '--dry-run',
              action='store_true',
              help='Show what will happen without doing anything.')

        a('-v', '--verbose', action='count', default=0, help='More output.')
        a('-q', '--quiet', action='count', default=0, help='Less output.')
        a('-T', '--traceback', action='store_true',
          help='Show full traceback.')

        if cmd in ['delete', 'resubmit']:
            a('-r', '--recursive', action='store_true',
              help='Use also subfolders.')
            a('folder',
              nargs='*',
              help='Task-folder.  Use --recursive (or -r) to include '
              'subfolders.')

        if cmd == 'list':
            a('folder',
              nargs='*',
              help='List tasks in this folder and its subfolders.  '
              'Defaults to current folder.')

        if cmd in ['submit', 'workflow']:
            a('folder',
              nargs='*', default=['.'],
              help='Submit tasks in this folder.  '
              'Defaults to current folder.')

    args = parser.parse_args(arguments)

    args.command = aliases.get(args.command, args.command)

    if args.command is None:
        parser.print_help()
        return

    if args.command == 'help':
        if args.cmd is None:
            parser.print_help()
        else:
            subparsers.choices[args.cmd].print_help()  # type: ignore
        return

    if args.command == 'test':
        from myqueue.test.tests import run_tests
        run_tests(args.test, args.slurm)
        return

    try:
        results = run(args)
        if arguments:
            return results
    except KeyboardInterrupt:
        pass
    except MyQueueCLIError as x:
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


def run(args):
    verbosity = 1 - args.quiet + args.verbose

    from pathlib import Path

    from myqueue.resources import Resources
    from myqueue.task import task, taskstates
    from myqueue.tasks import Tasks, Selection

    if args.command in ['list', 'submit', 'delete', 'resubmit', 'workflow']:
        folders = [Path(folder).expanduser().absolute().resolve()
                   for folder in args.folder]
        if args.command in ['delete', 'resubmit']:
            if not args.id and not folders:
                raise MyQueueCLIError('Missing folder!')

    if args.command in ['list', 'delete', 'resubmit']:
        default = 'qrdFCT' if args.command == 'list' else ''
        states = set()
        for s in args.states if args.states is not None else default:
            for state in taskstates:
                if s == state[0]:
                    states.add(state)
                    break
            else:
                raise MyQueueCLIError('Unknown state: ' + s)

        ids = None  # type: Set[int]
        if args.id:
            if args.states is not None:
                raise MyQueueCLIError("You can't use both -i and -s!")
            if len(args.folder) > 0:
                raise ValueError("You can't use both -i and folder(s)!")

            if args.id == '-':
                ids = {int(id) for id in sys.stdin}
            else:
                ids = {int(id) for id in args.id.split(',')}
        elif args.command != 'list' and args.states is None:
            raise MyQueueCLIError('You must use "-i <id>" OR "-s <state(s)>"!')

        if args.command == 'list' and not folders:
            folders = [Path.cwd()]

        selection = Selection(ids, args.name, states,
                              folders, getattr(args, 'recursive', True))

    with Tasks(verbosity) as tasks:
        if args.command == 'list':
            return tasks.list(selection, args.columns)

        if args.command == 'delete':
            tasks.delete(selection, args.dry_run)

        elif args.command == 'resubmit':
            if args.resources:
                resources = Resources.from_string(args.resources)
            else:
                resources = None
            tasks.resubmit(selection, args.dry_run, resources)

        elif args.command == 'submit':
            if args.arguments:
                arguments = args.arguments.split(',')
            else:
                arguments = []
            newtasks = [task(args.task,
                             args=arguments,
                             resources=args.resources,
                             folder=folder,
                             deps=args.dependencies,
                             workflow=args.workflow)
                        for folder in folders]

            tasks.submit(newtasks, args.dry_run)

        elif args.command == 'workflow':
            workflow(args, tasks, folders)
            return

        elif args.command == 'completion':
            cmd = ('complete -o default -C "{py} {filename}" mq'
                   .format(py=sys.executable,
                           filename=Path(__file__).with_name('complete.py')))
            if verbosity > 0:
                print('Add tab-completion for Bash by copying the following '
                      'line to your ~/.bashrc (or similar file):\n\n   {cmd}\n'
                      .format(cmd=cmd))
            else:
                print(cmd)


def workflow(args, tasks, folders):
    from pathlib import Path
    from myqueue.utils import chdir

    if args.pattern:
        workflow2(args, tasks, folders)
        return

    script = Path(args.script).read_text()
    code = compile(script, args.script, 'exec')
    namespace = {}
    exec(code, namespace)
    func = namespace['create_tasks']

    alltasks = []
    for folder in folders:
        with chdir(folder):
            newtasks = func()
        for task in newtasks:
            task.workflow = True

        alltasks += newtasks

    tasks.submit(alltasks, args.dry_run)


def workflow2(args, tasks, folders):
    from myqueue.utils import chdir

    alltasks = []
    for folder in folders:
        for path in folder.glob('**/*' + args.script):
            script = path.read_text()
            code = compile(script, str(path), 'exec')
            namespace = {}
            exec(code, namespace)
            func = namespace['create_tasks']

            with chdir(path.parent):
                newtasks = func()
            for task in newtasks:
                task.workflow = True

            alltasks += newtasks

    tasks.submit(alltasks, args.dry_run)
