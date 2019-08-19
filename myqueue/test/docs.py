import os
import re
import time
from pathlib import Path
from subprocess import run, PIPE
from typing import List, Tuple

import myqueue.test.testrunner as testrunner
from .testrunner import test, wait

user = os.environ.get('USER', 'root')


def run_document(path: Path, test=False) -> None:
    lines = path.read_text().splitlines()
    blocks: List[Tuple[str, List[str], int]] = []
    n = 0
    while n < len(lines):
        line = lines[n]
        if line.endswith('::') and lines[n + 2][:5] == '    $':
            cmd = ''
            output: List[str] = []
            L = 0
            for n, line in enumerate(lines[n + 2:], n + 2):
                if not line:
                    break
                if line[4] == '$':
                    if cmd:
                        blocks.append((cmd, output, L))
                    cmd = line[6:]
                    output = []
                    L = n
                else:
                    output.append(line)
            blocks.append((cmd, output, L))
        n += 1

    pypath = Path().absolute()
    offset = 0
    folder = '.'
    errors = 0
    for cmd, output, L in blocks:
        print('$', cmd)
        time.sleep(0.3)
        actual_output, folder = run_command(cmd, folder, pypath)
        wait()
        actual_output = ['    ' + line.replace('1:2s', '1:10m').rstrip()
                         for line in actual_output]
        errors += compare(output, actual_output)
        L += 1 + offset
        lines[L:L + len(output)] = actual_output
        offset += len(actual_output) - len(output)

    if testrunner.UPDATE:
        path.write_text('\n'.join(lines) + '\n')

    if test:
        assert errors == 0


def run_command(cmd: str,
                folder: str,
                pypath: Path) -> Tuple[List[str], str]:
    cmd, _, _ = cmd.partition('  #')
    result = run(f'export PYTHONPATH={pypath}; cd {folder}; {cmd}; pwd',
                 shell=True, check=True, stdout=PIPE)
    output = result.stdout.decode().splitlines()
    folder = output.pop()
    return output, folder


def clean(line):
    line = re.sub(r'[A-Z][a-z]+ [0-9]+ [0-9]+:[0-9]+', '############', line)
    line = re.sub(r' 0:[0-9][0-9]', ' 0:##', line)
    line = re.sub(r'[rw.-]{10,11}', '##########', line)
    line = re.sub(r' tot\w+ \d+', ' ##### #', line)
    line = re.sub(rf' {user} \w+ ', ' jensj ##### ', line)
    line = re.sub(r' jensj jensj ', ' jensj ##### ', line)
    return line


def compare(t1, t2):
    t1 = [clean(line) for line in t1]
    t2 = [clean(line) for line in t2]
    if t1 == t2:
        return 0
    print('<<<<<<<<<<<')
    print('\n'.join(t1))
    print('===========')
    print('\n'.join(t2))
    print('>>>>>>>>>>>')
    return 1


@test
def docs_workflows():
    dir = Path(__file__).parent / '../../docs'
    f = Path('.myqueue/queue.json')
    if f.is_file():
        f.unlink()
    Path('.myqueue/local.json').write_text('{"tasks": [], "number": 13}')
    p = Path('prime')
    p.mkdir()
    for f in dir.glob('prime/*.*'):
        (p / f.name).write_text(f.read_text())
    time.sleep(1)
    run_document(dir / 'workflows.rst', test=True)


@test
def docs_tutorial():
    dir = Path(__file__).parent / '../../docs'
    f = Path('.myqueue/queue.json')
    if f.is_file():
        f.unlink()
    Path('.myqueue/local.json').write_text('{"tasks": [], "number": 0}')
    run_document(dir / 'tutorial.rst', test=True)


@test
def docs_quickstart():
    dir = Path(__file__).parent / '../../docs'
    f = Path('.myqueue/queue.json')
    if f.is_file():
        f.unlink()
    Path('.myqueue/local.json').write_text('{"tasks": [], "number": 0}')
    run_document(dir / 'quickstart.rst', test=True)
