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

    possible_states = {'list': 'qrdFCT',
                       'resubmit': 'FCT',
                       'delete': 'qrdFCT'}

    for cmd, help in [
        ('help', 'Show how to use this tool.'),
        ('list', 'List jobs in queue.'),
        ('submit', 'Submit job(s) to queue.'),
        ('resubmit', 'Resubmit failed or timed-out jobs.'),
        ('workflow', 'Put many jobs in queue.'),
        ('delete', 'Delete or cancel job(s).'),
        ('agts', 'XXX')]:

        p = subparsers.add_parser(cmd, description=help, help=help,
                                  alias=cmd[0])

        if cmd == 'help':
            continue

        a = p.add_argument

        a('folder',
          nargs='*',
          help='List of folders.  Defaults to current '
          'folder and its folders and its folders and ...')

        if cmd == 'submit':
            a('script')
            a('-R', '--resources',
              help='Examples: "8x1h", 8 cores for 1 hour. '
              'Use "m" for minutes, '
              '"h" for hours and "d" for days.')
            a('-d', '--dependencies')
            a('-a', '--arguments')

        elif cmd == 'workflow':
            a('workflow', help='Work-flow description file.')

        states = possible_states.get(cmd)
        if states is not None:
            a('-s', '--states', metavar=states,
              default=states if cmd == 'list' else '',
              help='Selection of states. First letters of "{}".'
              .format('", "'.join(s for s in jobstates if s[0] in states)))
            a('-i', '--id', type=int)
            a('-n', '--name',
              help='Select only jobs named "NAME".')

        if cmd != 'list':
            a('-z', '--dry-run',
              action='store_true',
              help='Show what will happen before it happens.')

        a('-r', '--runner', default='slurm',
          help='Which queue to use: slurm or local.  Default '
          'is slurm.')

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

    queue = Queue(args.runner, verbosity)

    if args.command in possible_states:
        states = set()
        for s in args.states:
            assert s in possible_states[args.command]
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
                       deps=deps)
                   for folder in folders]

        queue.submit(newjobs, False, args.dry_run)

    elif args.command == 'delete':
        queue.delete(states, args.id, folders, args.dry_run)

    elif args.command == 'resubmit':
        queue.resubmit(states, args.id, folders, args.dry_run)

    elif args.command == 'workflow':
        _workflow['jobs'] = []
        code = Path(args.workflow).read_text()
        exec(compile(code, args.workflow, 'exec'))

        for folder in folders:
            for job in _workflow['jobs']:
                job.folder = folder
            queue.submit(_workflow['jobs'], True, args.dry_run)
