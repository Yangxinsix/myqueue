from __future__ import annotations


def parse_stderr(text: str) -> tuple[str, bool]:
    r"""Find error message in stderr text and check if it was an OOM error.

    >>> parse_stderr('OOM-kill')
    ('OOM-kill', True)
    >>> parse_stderr('raise SCFConvergenceError\n'
                     'Set MCA parameter "orte_base_help_aggregate" '
                     'to 0 to see all help / error messages')
    ('raise SCFConvergenceError', False)
    """
    lines = text.splitlines()
    for line in lines[::-1]:
        ll = line.lower()
        if any(x in ll for x in ['error:', 'memoryerror', 'malloc',
                                 'memory limit', 'oom-kill',
                                 'out of memory', 'assertionerror']):
            oom = (line.endswith('memory limit at some point.') or
                   'malloc' in line or
                   line.startswith('MemoryError') or
                   'oom-kill' in line or
                   line.endswith('out of memory'))
            return line, oom

    for line in lines:
        ll = line.lower()
        if 'error' in line:
            return line, False
    if lines:
        return lines[-1], False

    return '-', False
