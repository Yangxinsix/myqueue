import argparse
import subprocess
import sys
from pathlib import Path

from q2.job import Job, jobstates
from q2.jobs import Jobs
from q2.runner import get_runner
from q2.utils import chdir


class Queue:
    def __init__(self, queue):
        self.queue = queue
        self.jobs = []
        self.flags = set()
        self.folder = None
        self.done = set()

    def add(self, name, resources=None, deps=[], cores=1, time='1m',
            flow=False):
        if resources is not None:
            cores, time = resources.split('x')
            cores = int(cores)

        job = Job(name, deps, cores, time, self.folder, flow)

        if name in self.done:
            job.state = 'done'

        self.jobs.append(task)

        return job

    def update(self):
        jobs = self.queue.read()
        map = {j.uname: j for j in jobs.values()}
        for job in self.tasks:
            if job.state != 'UNKNOWN':
                assert job.state == 'done'
                assert job.uname not in map
                continue

            j = map.get(job.uname)
            if j is None:
                job.state = 'todo'
            else:
                job.state = j.state
                if job.state == 'running' and j.queue == 'slurm':
                    ...  # check for timeout


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
        '-d', '--done')

    # flow command:
    help = 'Put available jobs in queue.'
    workflow = subparsers.add_parser(
        'workflow',
        description=help,
        help=help)
    workflow.add_argument('-w', '--workflow', default='workflow.py',
                          help='Work-flow description file.  Default: '
                          'workflow.py.')
    # Reset subcommand:
    help = 'Reset state for job(s).'
    reset = subparsers.add_parser('reset',
                                  description=help,
                                  help=help)

    # Cancel subcommand:
    help = 'Cancel job(s).'
    cancel = subparsers.add_parser(
        'cancel',
        description=help,
        help=help)

    default = ','.join(s[0] for s in jobstates)

    # Common options:
    for p in [list_, submit, workflow, reset, cancel]:
        if p is not list_:
            p.add_argument('folder',
                           nargs='+',
                           help='List of folders.')
        p.add_argument('-f', '--filter',
                       help='Select only jobs named "TASK".')

        p.add_argument(
            '-s', '--states',
            metavar='STATE1,STATE2,...',
            default=default,
            help='Comma-separated list of states to show. '
            'Possible states: "{}".  First letter '
            'also works: "-s F,T" (same as "-s FAILED,TIMEOUT"). '
            'Default is "-s {}".'
            .format('", "'.join(jobstates), default))
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

    states = set()
    for s in args.states.split(','):
        for state in jobstates:
            if s == state or s == state[0]:
                break
        else:
            raise ValueError('Unknown state: ' + s)
        states.add(state)

    # n = self.queue.maxjobs
    # print('Can only submit {n} jobs!  Use "-N number" to increase the '
    #       'limit.'.format(n=n))

    if args.command == 'list':
        jobs.list(states)
        return

    if not args.dry_run:
        runner = get_runner(args.runner)

    if args.command == 'submit':
        for folder in args.folder:
            job = Job(args.script, folder=folder)
            if args.dry_run:
                print(job)
            else:
                jobs.submit(job, runner)
        if not args.dry_run:
            runner.kick()

    elif args.command == 'reset':
        for folder in folders(args.folder):
            with chdir(folder):
                append(args.job, args.state)

    elif args.command == 'run':
        name = args.job
        module, _, function = name.partition(':')
        for folder in folders(args.folder):
            with chdir(folder):
                cmd = 'python3 ' + command(module, function)
                if args.dry_run:
                    print(folder, cmd)
                else:
                    print(folder)
                    err = subprocess.call(cmd, shell=True)
                    if err:
                        append(name, 'FAILED')
                        break
                    append(name, 'done')

    elif args.command == 'cancel':
        ...
