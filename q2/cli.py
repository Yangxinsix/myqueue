import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(
        prog='q2',
        description='Manage jobs in queue.')

    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-q', '--quiet', action='store_true')
    parser.add_argument('-T', '--traceback', action='store_true')

    subparsers = parser.add_subparsers(dest='command')

    for cmd, help in [
        ('help', 'Show how to use this tool.'),
        ('list', 'List jobs in queue.'),
        ('submit', 'Submit job(s) to queue.'),
        ('resubmit', 'Resubmit failed or timed-out jobs.'),
        ('delete', 'Delete or cancel job(s).'),
        ('runner', 'Set runner.'),
        ('completion', 'Set up tab-completion.')]:

        p = subparsers.add_parser(cmd, description=help, help=help)

        if cmd == 'help':
            continue

        a = p.add_argument

        if cmd == 'runner':
            a('runner', help='Set runner to RUNNER (local or slurm).')

        elif cmd == 'submit':
            a('script')

            a('-d', '--dependencies')
            a('-a', '--arguments')
            a('-w', '--workflow', action='store_true')
            a('--convert', action='store_true')

        if cmd in ['resubmit', 'submit']:
            a('-R', '--resources',
              help='Examples: "8x1h", 8 cores for 1 hour. '
              'Use "m" for minutes, '
              '"h" for hours and "d" for days.')

        if cmd in ['list', 'delete', 'resubmit']:
            a('-s', '--states', metavar='qrdFCT',
              help='Selection of states. First letters of "queued", '
              '"running", "done", "FAILED", "CANCELED" and "TIMEOUT".')
            a('-i', '--id', type=int)
            a('-n', '--name',
              help='Select only jobs named "NAME".')

        if cmd != 'list':
            a('-z', '--dry-run',
              action='store_true',
              help='Show what will happen before it happens.')

        a('folder',
          nargs='*',
          help='List of folders.')

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    if 0:  # args.command in ['list', 'help'] and sys.stdout.isatty():
        # Pipe output through less:
        subprocess.run('python3 -m q2 ' +
                       ' '.join(sys.argv[1:]) + ' | less -FX',
                       shell=True)
        return

    try:
        run(args)
    except KeyboardInterrupt:
        pass
    except Exception as x:
        if args.traceback:
            raise
        else:
            print('{}: {}'.format(x.__class__.__name__, x),
                  file=sys.stderr)
            print('To get a full traceback, use: q2 -T {} ...'
                  .format(args.command), file=sys.stderr)


def run(args):
    verbosity = 1 - int(args.quiet) + int(args.verbose)

    from pathlib import Path

    from q2.job import Job, jobstates
    from q2.queue import Queue

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
            queue.list(args.id, args.name, states, folders)

        elif args.command == 'delete':
            queue.delete(args.id, args.name, states, folders, args.dry_run)

        elif args.command == 'resubmit':
            queue.resubmit(args.id, args.name, states, folders, args.dry_run)

        elif args.command == 'completion':
            print('Add tab-completion for Bash by copying the following '
                  'line to your ~/.bashrc (or similar):\n')
            print('    complete -o default -C "{py} {filename}" q2\n'
                  .format(py=sys.executable,
                          filename=Path(__file__).with_name('complete.py')))

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

            if args.resources:
                cores, tmax = args.resources.slpit('x')
            else:
                cores = None
                tmax = None

            if args.arguments:
                arguments = args.arguments.split(',')
            else:
                arguments = None
            newjobs = [Job(args.script,
                           args=arguments,
                           tmax=tmax,
                           cores=cores,
                           folder=folder,
                           deps=deps)
                       for folder in folders]

            queue.submit(newjobs, args.dry_run)


def workflow(args, queue, folders):
    from pathlib import Path
    from q2.job import _workflow
    from q2.utils import chdir

    _workflow['jobs'] = []
    script = Path(args.script).read_text()
    code = compile(script, args.script, 'exec')
    jobs = _workflow['jobs']

    if not folders:
        folders = [Path('.')]

    alljobs = []
    for folder in folders:
        with chdir(folder.expanduser()):
            exec(code)  # magically fills up jobs from workflow script
        for job in jobs:
            job.folder = folder
            job.workflow = True

        if args.convert:
            convert_dot_tasks_file(jobs, folder.expanduser())
        else:
            alljobs += jobs

        del jobs[:]  # ready for next exec(code) call

    if not args.convert:
        queue.submit(alljobs, args.dry_run)


def convert_dot_tasks_file(jobs, folder):
    from pathlib import Path
    tasks = Path(folder / '.tasks')
    if tasks.is_file():
        done = {}
        for line in tasks.read_text().splitlines():
            date, state, name, *_ = line.split()
            done[name] = (state == 'done')
        for job in jobs:
            if done.get(job.cmd.name):
                d = folder / (job.cmd.name + '.done')
                d.write_text('')
                print(d)
