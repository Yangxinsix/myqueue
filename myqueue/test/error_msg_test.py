import pytest
from myqueue.errors import parse_stderr

err1 = """
L00: Traceback (most recent call last):
...
L17: ModuleNotFoundError: No module named 'gpaw.bz_tools'
e>
 at line 2193
[x069] PMIX ERROR: UNREACHABLE in file server/pmix_server.c at line 2193
[x069] PMIX ERROR: UNREACHABLE in file server/pmix_server.c at line 2193
[x069] 47 more processes have sent help message help-mpi-api.txt / mpi-abort
[x069] Set MCA ... "orte_base_help_aggregate" to 0 to see all help / error msg
"""

err2 = """\
-------------------------------------------------------------------------
Primary job  terminated normally, but 1 process returned
a non-zero exit code. Per user-direction, the job has been aborted.
--------------------------------------------------------------------------
--------------------------------------------------------------------------
mpiexec noticed that process rank 73 with PID 4058 on node a042 exited on \
signal 9 (Killed).
--------------------------------------------------------------------------
slurmstepd: error: Detected 3 oom_kill events in StepId=7351576.batch. \
Some of the step tasks have been OOM Killed.
"""

err3 = """\
slurmstepd: error: _get_joules_task: can't get info from slurmd
Traceback (most recent call last):
  File "/home/.../iron/../../electronic/dos/pdos.py", line 10, in <module>
    energies, ldos = calc.get_orbital_ldos(a=0, spin=0, angular=c, width=0.4)
                     ^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'ASECalculator' object has no attribute 'get_orbital_ldos'
slurmstepd: error: _get_joules_task: can't get info from slurmd
slurmstepd: error: _get_joules_task: can't get info from slurmd
"""


@pytest.mark.parametrize(
    'err, line, oom',
    [(err1, 'L17: ModuleNotFoundError:', False),
     (err2, 'slurmstepd: error: Detected 3 oom_kill events', True),
     (err3, "AttributeError: 'ASECalculator' object has no", False)])
def test_niflheim_error(err, line, oom):
    line1, oom1 = parse_stderr(err)
    assert oom1 == oom
    print(line)
    print(line1)
    assert line1.startswith(line)
