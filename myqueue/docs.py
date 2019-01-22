from pathlib import Path
from subprocess import run, PIPE
from typing import List, Tuple


def run_document(path: Path) -> None:
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

    offset = 0
    folder = '.'
    for cmd, output, L in blocks:
        print('$', cmd)
        actual_output, folder = run_command(cmd, folder)
        actual_output = [line.replace('1:2s', '1:10m').rstrip()
                         for line in actual_output]
        if actual_output:
            print('\n'.join(actual_output))
        L += 1 + offset
        lines[L:L + len(output)] = ('    ' + line for line in actual_output)
        offset += len(actual_output) - len(output)

    path.write_text('\n'.join(lines) + '\n')


def run_command(cmd: str,
                folder: str) -> Tuple[List[str], str]:
    cmd, _, _ = cmd.partition('  #')
    result = run(f'cd {folder}; {cmd}; pwd',
                 shell=True, check=True, stdout=PIPE)
    output = result.stdout.decode().splitlines()
    folder = output.pop()
    return output, folder


if __name__ == '__main__':
    import sys
    run_document(Path(sys.argv[1]))
