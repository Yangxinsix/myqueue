import argparse
import subprocess
import sys
from pathlib import Path

from q2.job import Job, jobstates, _workflow
from q2.jobs import Jobs
from q2.runner import get_runner


def main():
    parser = argparse.ArgumentParser(
        prog='q2',
        description='Manage jobs in queue.')

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-q', '--quiet', action='store_true')

    subparsers = parser.add_subparsers(dest='command')

    # List subcommand:
    help = 'List jobs in queue.'
    list_ = subparsers.add_parser('list',
                                  description=help,
                                  help=help)
    list_.add_argument(
        'folder',
        nargs='*',
        help='List of folders.  Defaults to current '
        'folder and its folders and its folders and ...')

    # Submit subcommand:
    help = 'Submit job(s) to queue.'
    submit = subparsers.add_parser(
        'submit',
        description=help,
        help=help)
    submit.add_argument('script')
    submit.add_argument(
        '-R', '--resources',
        help='Examples: "8x1h", 8 cores for 1 hour. Use "m" for minutes, '
        '"h" for hours and "d" for days.')
    submit.add_argument(
        '-d', '--dependencies')

    # flow command:
    help = 'Put many jobs in queue.'
    workflow = subparsers.add_parser(
        'workflow',
        description=help,
        help=help)
    workflow.add_argument('workflow',
                          help='Work-flow description file.')

    # Reset subcommand:
    help = 'Reset state for job(s).'
    reset = subparsers.add_parser('reset',
                                  description=help,
                                  help=help)
    reset.add_argument('-S', '--resubmit', action='store_true')
    reset.add_argument('-i', '--id', type=int)

    # Cancel subcommand:
    help = 'Cancel job(s).'
    cancel = subparsers.add_parser(
        'cancel',
        description=help,
        help=help)

    default_states = {'list': 'qrFCT',
                      'reset': 'FCT',
                      'cancel': 'qr'}

    # Common options:
    for p in [list_, submit, workflow, reset, cancel]:
        if p is not list_:
            p.add_argument('folder',
                           nargs='+',
                           help='List of folders.')
        p.add_argument('-f', '--filter',
                       help='Select only jobs named "TASK".')

        if p is list_:
            default = default_states['list']
        elif p is reset:
            default = default_states['reset']

        elif p is cancel:
            default = default_states['cancel']
        else:
            default = ''

        if default:
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

    jobs = Jobs(verbosity)

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
        jobs.list(states)

    elif args.command == 'submit':
        deps = []
        if args.dependencies:
            for dep in args.dependencies.split(','):
                reldir, _, script = dep.rpartition('/')
                if not reldir:
                    reldir = '.'
                deps.append((script, reldir))

        newjobs = [Job(args.script, folder=folder, deps=deps)
                   for folder in folders]

        # n = self.queue.maxjobs
        # print('Can only submit {n} jobs!  Use "-N number" to increase the '
        #       'limit.'.format(n=n))
        runner = get_runner(args.runner)
        jobs.submit(newjobs, runner, args.dry_run)

    elif args.command == 'reset':
        jobs.reset(states, args.id, folders, args.resubmit, args.dry_run)

    elif args.command == 'cancel':
        ...

    elif args.command == 'workflow':
        _workflow['jobs'] = []
        code = Path(args.workflow).read_text()
        exec(compile(code, args.workflow, 'exec'))

        runner = get_runner(args.runner)

        for folder in folders:
            for job in _workflow['jobs']:
                job.folder = folder
            jobs.submit(_workflow['jobs'], runner, args.dry_run)
