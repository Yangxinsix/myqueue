import argparse
import subprocess
import sys
from typing import List, Any


intro = """
Jobs
====

A job can be one of these:

* a Python script (job.py)
* a Python module (module)
* a function in a Python module (module.function)
* an executable or shell-script

Examples
========

Run job.py on 8 cores for 1 hour in folder1 and folder2:

    $ mq submit job.py@8x10h folder1/ folder2/

Sleep for 25 seconds on 1 core using the time.sleep() function:

    $ mq submit time.sleep -a 25 -R 1x1m

or equivalently:

    $ mq submit time.sleep+25@1x1m

Say "hello" (using the defaults of 1 core for 10 minutes):

    $ mq submit echo -a hello

You can see the status of your jobs with:

    $ mq list
    id folder name       res.   age state time error
    -- ------ ---------- ----- ---- ----- ---- -----
    1  ~      echo+hello 1x10m 0:06 done  0:00
    -- ------ ---------- ----- ---- ----- ---- -----
    done: 1

Delete the job from the list with:

    $ mq delete -s d .

The output from the job will be in ~/echo+hello.1.out and
~/echo+hello.1.err (if there was any output).

    $ cat echo+hello.1.out
    hello

If a job fails or times out, then you can resubmit it with more resources:

    $ mq submit sleep+3000@1x30m
    ...
    $ mq list
    id folder name       res.   age state   time  error
    -- ------ ---------- ----- ---- ------- ----- -----
    2  ~      sleep+3000 1x30m 1:16 TIMEOUT 50:00
    -- ------ ---------- ----- ---- ------- ----- -----
    TIMEOUT: 1
    $ mq resubmit -i 2 -R 1x1h


Tab-completion
==============

    $ mq completions -q >> ~/.bashrc

"""


class MyQueueCLIError(Exception):
    pass


def main(arguments: List[str] = None) -> Any:
    parser = argparse.ArgumentParser(
        prog='mq',
        description='Manage jobs in queue.')

    subparsers = parser.add_subparsers(title='Commands', dest='command')

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
            a('test', nargs='*',
              help='Test to run.  Default behaviour is to run all.')

        elif cmd == 'submit':
            a('script')
            a('-d', '--dependencies')
            a('-a', '--arguments')

        if cmd in ['resubmit', 'submit']:
            a('-R', '--resources',
              help='Examples: "8x1h", 8 cores for 1 hour. '
              'Use "m" for minutes, '
              '"h" for hours and "d" for days. '
              '"16:1x30m": 16 cores, 1 process, half an hour.')
            a('-w', '--workflow', action='store_true',
              help='Write <job-name>.done file when done.')

        if cmd == 'workflow':
            a('script')
            a('-p', '--pattern', action='store_true')

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
              help='Show what will happen without doing anything.')

        a('-v', '--verbose', action='count', default=0, help='More output.')
        a('-q', '--quiet', action='count', default=0, help='Less output.')
        a('-T', '--traceback', action='store_true',
          help='Show full traceback.')

        if cmd in ['delete', 'resubmit']:
            a('-r', '--recursive', action='store_true')
            a('folder',
              nargs='*',
              help='Job-folder.  Use --recursive (or -r) to include '
              'subfolders.')

        if cmd == 'list':
            a('folder',
              nargs='*', default=['.'],
              help='List jobs in this folder and its subfolders.  '
              'Defaults to current folder.')

        if cmd in ['submit', 'workflow']:
            a('folder',
              nargs='*', default=['.'],
              help='Submit jobs in this folder.  '
              'Defaults to current folder.')

    args = parser.parse_args(arguments)

    args.command = aliases.get(args.command, args.command)

    if args.command is None:
        parser.print_help()
        return

    if args.command == 'help' and sys.stdout.isatty():
        # Pipe output through less:
        subprocess.run('python3 -m myqueue ' +
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
                  .format(name.title(), '=' * (len(name) + 8)))
            p.print_help()
        return

    if args.command == 'test':
        from myqueue.test.tests import run_tests
        run_tests(args.test)
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

    from myqueue.job import Job, jobstates, T, parse_resource_string
    from myqueue.queue import Queue

    if args.command == 'runner':
        (Path.home() / '.myqueue' / 'runner').write_text(args.runner)
        return

    path = Path.home() / '.myqueue' / 'runner'
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
                raise MyQueueCLIError('Unknown state: ' + s)

        if args.id:
            if args.states is not None:
                raise MyQueueCLIError("You can't use both -i and -s!")
            if len(args.folder) > 0:
                raise ValueError("You can't use both -i and folder(s)!")
        elif args.command != 'list' and args.states is None:
            raise MyQueueCLIError('You must use "-i <id>" OR "-s <state(s)>"!')

    if args.command in ['list', 'submit', 'delete', 'resubmit', 'workflow']:
        folders = [Path(folder).expanduser().absolute().resolve()
                   for folder in args.folder]
        if args.command in ['delete', 'resubmit']:
            if not args.id and not folders:
                raise MyQueueCLIError('Missing folder!')

    if args.command in ['submit', 'resubmit']:
        if args.resources:
            cores, processes, tmax = parse_resource_string(args.resources)
            tmax = T(tmax)
        else:
            cores = None
            processes = None
            tmax = None

    with Queue(runner, verbosity) as queue:

        if args.command == 'list':
            jobs = queue.list(args.id, args.name, states, folders,
                              args.columns)
            return jobs

        if args.command == 'delete':
            queue.delete(args.id, args.name, states, folders, args.recursive,
                         args.dry_run)

        elif args.command == 'resubmit':
            queue.resubmit(args.id, args.name, states, folders, args.recursive,
                           args.dry_run, cores, processes, tmax)

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
                           processes=processes,
                           folder=folder,
                           deps=deps,
                           workflow=args.workflow)
                       for folder in folders]

            queue.submit(newjobs, args.dry_run)

        elif args.command == 'workflow':
            workflow(args, queue, folders)
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


def workflow(args, queue, folders):
    from pathlib import Path
    from myqueue.utils import chdir

    if args.pattern:
        workflow2(args, queue, folders)
        return

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


def workflow2(args, queue, folders):
    from myqueue.utils import chdir

    alljobs = []
    for folder in folders:
        for path in folder.glob('**/*' + args.script):
            script = path.read_text()
            code = compile(script, path, 'exec')
            namespace = {}
            exec(code, namespace)
            func = namespace['workflow']

            with chdir(path.parent):
                jobs = func()
            for job in jobs:
                job.folder = path.parent
                job.workflow = True

            alljobs += jobs

    queue.submit(alljobs, args.dry_run)
