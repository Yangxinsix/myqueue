import argparse
import subprocess
import sys
from pathlib import Path

from q2.job import Job, jobstates, _workflow
from q2.queue import Queue
from q2.runner import get_runner


def main():
    parser = argparse.ArgumentParser(
        prog='q2',
        description='Manage jobs in queue.')

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-q', '--quiet', action='store_true')

    subparsers = parser.add_subparsers(dest='command')

    default_states = {'list': 'qrFCT',
                      'reset': 'FCT',
                      'cancel': 'qr'}

    for cmd, help in [
        ('list', 'List jobs in queue.'),
        ('submit', 'Submit job(s) to queue.'),
        ('workflow', 'Put many jobs in queue.'),
        ('reset', 'Reset state for job(s).'),
        ('cancel', 'Cancel job(s).')]:

        p = subparsers.add_parser(cmd, description=help, help=help)

        if cmd == 'list':
            p.add_argument(
                'folder',
                nargs='*',
                help='List of folders.  Defaults to current '
                'folder and its folders and its folders and ...')

        elif cmd == 'submit':
            p.add_argument('script')
            p.add_argument(
                '-R', '--resources',
                help='Examples: "8x1h", 8 cores for 1 hour. '
                'Use "m" for minutes, '
                '"h" for hours and "d" for days.')
            p.add_argument(
                '-d', '--dependencies')

        elif cmd == 'workflow':
            p.add_argument('workflow',
                           help='Work-flow description file.')

        elif cmd == 'reset':
            p.add_argument('-S', '--resubmit', action='store_true')

        if cmd in ['cancel', 'list', 'reset']:
            p.add_argument('-i', '--id', type=int)

        if cmd != 'list':
            p.add_argument('folder',
                           nargs='+',
                           help='List of folders.')

        if 0:
            p.add_argument('-f', '--filter',
                           help='Select only jobs named "TASK".')

        if cmd in default_states:
            default = default_states[cmd]
            p.add_argument(
                '-s', '--states',
                metavar=default,
                default=default,
                help='States to show. First letters of "{}".'
                .format('", "'.join(s for s in jobstates if s[0] in default)))

        p.add_argument('-n', '--dry-run',
                       action='store_true',
                       help='Show what will happen before it happens.')
        p.add_argument('-r', '--runner', default='slurm',
                       help='Which queue to use: slurm or local.  Default '
                       'is slurm.')
        p.add_argument('-N', '--number-of-jobs',
                       type=int,
                       default=1000)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if args.command == 'list' and sys.stdout.isatty():
        # Pipe output through less:
        subprocess.run('python3 -m q2 ' +
                       ' '.join(sys.argv[1:]) + ' | less -FX',
                       shell=True)
        return

    verbosity = 1 - int(args.quiet) + int(args.verbose)

    queue = Queue(verbosity)

    if args.command in default_states:
        states = set()
        for s in args.states:
            assert s in default_states[args.command]
            for state in jobstates:
                if s == state[0]:
                    states.add(state)
                    break
            else:
                raise ValueError('Unknown state: ' + s)

    home = Path.home()
    folders = ['~' / Path(folder).absolute().relative_to(home)
               for folder in args.folder]

    if args.command == 'list':
        queue.list(states)

    elif args.command == 'submit':
        deps = []
        if args.dependencies:
            for dep in args.dependencies.split(','):
                reldir, _, script = dep.rpartition('/')
                if not reldir:
                    reldir = '.'
                deps.append((script, reldir))

        newjobs = [Job(args.script,
                       folder=folder,
                       deps=deps,
                       runner=args.runner)
                   for folder in folders]

        # n = self.queue.maxjobs
        # print('Can only submit {n} jobs!  Use "-N number" to increase the '
        #       'limit.'.format(n=n))
        runner = get_runner(args.runner)
        queue.submit(newjobs, runner, args.dry_run)

    elif args.command == 'reset':
        queue.reset(states, args.id, folders, args.resubmit, args.dry_run)

    elif args.command == 'cancel':
        queue.cancel(states, args.id, folders, args.dry_run)

    elif args.command == 'workflow':
        _workflow['jobs'] = []
        code = Path(args.workflow).read_text()
        exec(compile(code, args.workflow, 'exec'))

        runner = get_runner(args.runner)

        for folder in folders:
            for job in _workflow['jobs']:
                job.folder = folder
            queue.submit(_workflow['jobs'], runner, args.dry_run)
