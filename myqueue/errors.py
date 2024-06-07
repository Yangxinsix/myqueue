from __future__ import annotations

import sys
from pathlib import Path


def parse_stderr(text: str) -> tuple[str, bool]:
    r"""Find error message in stderr text and check if it was an OOM error.

    >>> parse_stderr('OOM-kill')
    ('OOM-kill', True)
    >>> parse_stderr('raise SCFConvergenceError\n'
    ...              'Set MCA parameter "orte_base_help_aggregate" '
    ...              'to 0 to see all help / error messages')
    ('raise SCFConvergenceError', False)
    >>> parse_stderr('Bla-bla')
    ('Bla-bla', False)
    >>> parse_stderr('')
    ('-', False)
    """
    lines = text.splitlines()
    oom = False
    for line in lines[::-1]:
        ll = line.lower()
        if any(x in ll for x in ['error:', 'memoryerror', 'malloc',
                                 'memory limit', 'oom-kill', 'oom_kill',
                                 'out of memory', 'assertionerror']):
            oom = (ll.endswith('memory limit at some point.') or
                   'malloc' in ll or
                   line.startswith('MemoryError') or
                   'oom-kill' in ll or
                   'oom_kill' in ll or
                   line.endswith('out of memory'))
            break

    for line in lines:
        if 'Error:' in line:
            return line, oom
    for line in lines:
        ll = line.lower()
        if 'error' in ll:
            return line, oom
    if lines:
        return lines[-1], oom

    return '-', False


if __name__ == '__main__':
    txt, err = parse_stderr(Path(sys.argv[1]).read_text())
    print(txt)
    print('OOM:', err)
