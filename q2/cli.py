import argparse
import subprocess
import sys
from pathlib import Path

from q2.job import Job, jobstates, _workflow
from q2.queue import Queue
from q2.utils import chdir


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
        ('delete', 'Delete or cancel job(s).'),
        ('runner', 'Set runner.'),
        ('agts', 'XXX')]:

        p = subparsers.add_parser(cmd, description=help, help=help)

        if cmd == 'help':
            continue

        a = p.add_argument

        a('folder',
          nargs='*',
          help='List of folders.')

        if cmd == 'runner':
            a('runner', help='Set runner to RUNNER (local or slurm).')

        elif cmd == 'submit':
            a('script', nargs='?')
            a('-R', '--resources',
              help='Examples: "8x1h", 8 cores for 1 hour. '
              'Use "m" for minutes, '
              '"h" for hours and "d" for days.')
            a('-d', '--dependencies')
            a('-a', '--arguments')
            a('-w', '--workflow')

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

    with Queue(runner, verbosity) as queue:

        if args.command == 'list':
            queue.list(args.id, states, folders)

        elif args.command == 'delete':
            queue.delete(args.id, states, folders, args.dry_run)

        elif args.command == 'resubmit':
            queue.resubmit(args.id, states, folders, args.dry_run)

        elif args.command == 'submit':
            if args.workflow:
                workflow(args, queue, folders)
                return

            if args.dependencies:
                deps = args.dependencies.split(',')
            else:
                deps = []

            if not folders:
                folders = [Path('.')]

            newjobs = [Job(args.script,
                           folder=folder,
                           deps=deps)
                       for folder in folders]

            queue.submit(newjobs, args.dry_run)


def workflow(args, queue, folders):
    _workflow['jobs'] = []
    filename = args.workflow
    script = Path(filename).read_text()
    code = compile(script, filename, 'exec')
    jobs = _workflow['jobs']

    if not folders:
        folders = [Path('.')]

    alljobs = []
    for folder in folders:
        with chdir(folder):
            exec(code)  # magically fills up jobs from workflow script

        for job in jobs:
            job.folder = folder
            job.workflow = True

        if args.convert:
            convert_dot_tasks_file(jobs, folder)
        else:
            alljobs += jobs

        del jobs[:]  # ready for next exec(code) call

    if not args.convert:
        queue.submit(jobs, args.dry_run)


def convert_dot_tasks_file(jobs, folder):
    tasks = Path(folder / '.tasks')
    if tasks.is_file():
        done = {}
        for line in tasks.read_text().splitlines():
            date, state, name, *_ = line.split()
            done[name] = (state == 'done')
        for job in jobs:
            if done.get(job.cmd.name):
                d = folder / (job.cmd.name + '.done')
                d.write_text()
                print(d)
