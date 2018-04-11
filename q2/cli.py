import argparse
import subprocess
import sys
from typing import List, Any


intro = """
Examples:

    q2 submit job.py@8x10h folder*/
    q2 submit time.sleep -a 25 -R 1x1m
    q2 submit time.sleep+25@1x1m
    q2 submit echo -a hello
    q2 submit module
    q2 submit module.function
    q2 list
    q2 list -F
    q2 delete -s F
    q2 help submit
    q2 completions -q >> ~/.bashrc
    q2 resubmit -R 64x2d -n long_job.py

"""


def main(arguments: List[str] = None) -> Any:
    parser = argparse.ArgumentParser(
        prog='q2',
        description='Manage jobs in queue.')

    subparsers = parser.add_subparsers(dest='command')

    aliases = {'rm': 'delete',
               'ls': 'list'}

    for cmd, help in [('help', 'Show how to use this tool.'),
                      ('list', 'List jobs in queue.'),
                      ('submit', 'Submit job(s) to queue.'),
                      ('resubmit', 'Resubmit failed or timed-out jobs.'),
                      ('delete', 'Delete or cancel job(s).'),
                      ('workflow', 'Submit jobs from Python script.'),
                      ('runner', 'Set runner.'),
                      ('completion', 'Set up tab-completion.'),
                      ('test', 'Run tests.')]:

        p = subparsers.add_parser(cmd, description=help, help=help,
                                  aliases=[alias for alias in aliases
                                           if aliases[alias] == cmd])
        if cmd == 'help':
            continue

        a = p.add_argument

        if cmd == 'runner':
            a('runner', help='Set runner to RUNNER (local or slurm).')

        if cmd == 'test':
            a('tests', nargs='*',
              help='Which tests to run.  Default behaviour is to run all.')

        elif cmd == 'submit':
            a('script')
            a('-d', '--dependencies')
            a('-a', '--arguments')

        if cmd in ['resubmit', 'submit']:
            a('-R', '--resources',
              help='Examples: "8x1h", 8 cores for 1 hour. '
              'Use "m" for minutes, '
              '"h" for hours and "d" for days.')
            a('-w', '--workflow', action='store_true',
              help='Write <job-name>.done file when done.')

        if cmd == 'workflow':
            a('script')

        if cmd in ['list', 'delete', 'resubmit']:
            a('-s', '--states', metavar='qrdFCT',
              help='Selection of states. First letters of "queued", '
              '"running", "done", "FAILED", "CANCELED" and "TIMEOUT".')
            a('-i', '--id', type=int)
            a('-n', '--name',
              help='Select only jobs named "NAME".')

        if cmd == 'list':
            a('-c', '--columns', metavar='ifnraste', default='ifnraste',
              help='Select columns to show.')

        if cmd not in ['list', 'completion']:
            a('-z', '--dry-run',
              action='store_true',
              help='Show what will happen before it happens.')

        a('-v', '--verbose', action='count', default=0, help='More output.')
        a('-q', '--quiet', action='count', default=0, help='Less output.')
        a('-T', '--traceback', action='store_true',
          help='Show full traceback.')

        if cmd in ['delete', 'resubmit']:
            a('-r', '--recursive', action='store_true')

        if cmd in ['list', 'submit', 'delete', 'resubmit', 'workflow']:
            a('folder',
              nargs='*',
              help='List of folders.  Defaults to current folder.')

    args = parser.parse_args(arguments)

    args.command = aliases.get(args.command, args.command)

    if args.command is None:
        parser.print_help()
        return

    if args.command == 'help' and sys.stdout.isatty():
        # Pipe output through less:
        subprocess.run('python3 -m q2 ' +
                       ' '.join(sys.argv[1:]) + ' | less -FX',
                       shell=True)
        return

    if args.command == 'help':
        parser.print_help()
        print(intro)
        for name, p in subparsers.choices.items():  # type: ignore
            if name in ['help', 'rm', 'ls']:
                continue
            print('\n\n{} command\n{}\n'
                  .format(name.upper(), '=' * (len(name) + 8)))
            p.print_help()
        return

    if args.command == 'test':
        from q2.test.tests import run_tests
        run_tests(args.tests)
        return

    try:
        results = run(args)
        if arguments:
            return results
    except KeyboardInterrupt:
        pass
    except Exception as x:
        if args.traceback:
            raise
        else:
            print('{}: {}'.format(x.__class__.__name__, x),
                  file=sys.stderr)
            print('To get a full traceback, use: q2 {} ... -T'
                  .format(args.command), file=sys.stderr)
            return 1


def run(args):
    verbosity = 1 - args.quiet + args.verbose

    from pathlib import Path

    from q2.job import Job, jobstates, T
    from q2.queue import Queue

    if args.command == 'runner':
        (Path.home() / '.q2' / 'runner').write_text(args.runner)
        return

    path = Path.home() / '.q2' / 'runner'
    if path.is_file():
        runner = path.read_text()
    else:
        runner = 'local'

    if args.command in ['list', 'delete', 'resubmit']:
        default = 'qrdFCT' if args.command == 'list' else ''
        states = set()
        for s in args.states if args.states is not None else default:
            for state in jobstates:
                if s == state[0]:
                    states.add(state)
                    break
            else:
                raise ValueError('Unknown state: ' + s)

        if args.id:
            if args.states is not None:
                raise ValueError("You can't use both -i and -s!")
            if len(args.folder) > 0:
                raise ValueError("You can't use both -i and folder(s)!")

    if args.command in ['list', 'submit', 'delete', 'resubmit', 'workflow']:
        folders = [Path(folder).expanduser().absolute().resolve()
                   for folder in args.folder or ['.']]

    if args.command in ['submit', 'resubmit']:
        if args.resources:
            cores, tmax = args.resources.split('x')
            cores = int(cores)
            tmax = T(tmax)
        else:
            cores = None
            tmax = None

    with Queue(runner, verbosity) as queue:

        if args.command == 'list':
            jobs = queue.list(args.id, args.name, states, folders)
            return jobs

        if args.command == 'delete':
            queue.delete(args.id, args.name, states, folders, args.recursive,
                         args.dry_run)

        elif args.command == 'resubmit':
            queue.resubmit(args.id, args.name, states, folders, args.recursive,
                           args.dry_run, cores, tmax)

        elif args.command == 'submit':
            if args.dependencies:
                deps = args.dependencies.split(',')
            else:
                deps = []

            if args.arguments:
                arguments = args.arguments.split(',')
            else:
                arguments = None
            newjobs = [Job(args.script,
                           args=arguments,
                           tmax=tmax,
                           cores=cores,
                           folder=folder,
                           deps=deps,
                           workflow=args.workflow)
                       for folder in folders]

            queue.submit(newjobs, args.dry_run)

        elif args.command == 'workflow':
            workflow(args, queue, folders)
            return

        elif args.command == 'completion':
            cmd = ('complete -o default -C "{py} {filename}" q2'
                   .format(py=sys.executable,
                           filename=Path(__file__).with_name('complete.py')))
            if verbosity > 0:
                print('Add tab-completion for Bash by copying the following '
                      'line to your ~/.bashrc (or similar file):\n\n   {cmd}\n'
                      .format(cmd=cmd))
            else:
                print(cmd)


def workflow(args, queue, folders):
    from pathlib import Path
    from q2.utils import chdir

    script = Path(args.script).read_text()
    code = compile(script, args.script, 'exec')
    namespace = {}
    exec(code, namespace)
    func = namespace['workflow']

    alljobs = []
    for folder in folders:
        with chdir(folder):
            jobs = func()
        for job in jobs:
            job.folder = folder
            job.workflow = True

        alljobs += jobs

    queue.submit(alljobs, args.dry_run)
