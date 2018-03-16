import argparse
import subprocess
import sys
from pathlib import Path

from q2.job import Job, jobstates, _workflow
from q2.queue import Queue


def main():
    parser = argparse.ArgumentParser(
        prog='q2',
        description='Manage jobs in queue.')

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-q', '--quiet', action='store_true')

    subparsers = parser.add_subparsers(dest='command')

    for cmd, help in [
        ('help', 'Show how to use this tool.'),
        ('list', 'List jobs in queue.'),
        ('submit', 'Submit job(s) to queue.'),
        ('resubmit', 'Resubmit failed or timed-out jobs.'),
        ('workflow', 'Put many jobs in queue.'),
        ('delete', 'Delete or cancel job(s).'),
        ('runner', 'Set runner.'),
        ('kick', 'XXX'),
        ('agts', 'XXX')]:

        p = subparsers.add_parser(cmd, description=help, help=help)

        if cmd == 'help':
            continue

        a = p.add_argument

        a('folder',
          nargs='*',
          help='List of folders.  Defaults to current '
          'folder and its folders and its folders and ...')

        if cmd == 'runner':
            a('runner', help='Set runner to RUNNER (local or slurm).')

        elif cmd == 'submit':
            a('script')
            a('-R', '--resources',
              help='Examples: "8x1h", 8 cores for 1 hour. '
              'Use "m" for minutes, '
              '"h" for hours and "d" for days.')
            a('-d', '--dependencies')
            a('-a', '--arguments')

        elif cmd == 'workflow':
            a('workflow', help='Work-flow description file.')

        if cmd in ['list', 'delete', 'resubmit']:
            a('-s', '--states', metavar='qrdFCT',
              help='Selection of states. First letters of "{}".'
              .format('", "'.join(s for s in jobstates if s[0] in 'qrdFCT')))
            a('-i', '--id', type=int)
            a('-n', '--name',
              help='Select only jobs named "NAME".')

        if cmd != 'list':
            a('-z', '--dry-run',
              action='store_true',
              help='Show what will happen before it happens.')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command in ['list', 'help'] and sys.stdout.isatty():
        # Pipe output through less:
        subprocess.run('python3 -m q2 ' +
                       ' '.join(sys.argv[1:]) + ' | less -FX',
                       shell=True)
        return

    verbosity = 1 - int(args.quiet) + int(args.verbose)

    if args.command == 'runner':
        (Path.home() / '.q2' / 'runner').write_text(args.runner)
        return

    path = Path.home() / '.q2' / 'runner'
    if path.is_file():
        runner = path.read_text()
    else:
        runner = 'local'

    queue = Queue(runner, verbosity)

    if args.command == 'kick':
        queue.kick()
        return

    home = Path.home()
    folders = ['~' / Path(folder).absolute().relative_to(home)
               for folder in args.folder]

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
            assert args.states is None and len(folders) == 0

    if args.command == 'list':
        queue.list(args.id, states, folders)

    elif args.command == 'submit':
        deps = []
        if args.dependencies:
            for dep in args.dependencies.split(','):
                reldir, _, script = dep.rpartition('/')
                if not reldir:
                    reldir = '.'
                deps.append((script, reldir))

        if not folders:
            folders = [Path('.')]

        newjobs = [Job(args.script,
                       folder=folder,
                       deps=deps)
                   for folder in folders]

        queue.submit(newjobs, args.dry_run)

    elif args.command == 'delete':
        queue.delete(args.id, states, folders, args.dry_run)

    elif args.command == 'resubmit':
        queue.resubmit(args.id, states, folders, args.dry_run)

    elif args.command == 'workflow':
        _workflow['jobs'] = []
        code = Path(args.workflow).read_text()
        exec(compile(code, args.workflow, 'exec'))

        if not folders:
            folders = [Path('.')]

        for folder in folders:
            for job in _workflow['jobs']:
                job.folder = folder
                job.workflow = True
            queue.submit(_workflow['jobs'], args.dry_run)
