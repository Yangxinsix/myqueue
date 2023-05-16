from myqueue.errors import parse_stderr
from pathlib import Path
txt = """
rank=02 L00: Traceback (most recent call last):
...
rank=02 L17: ModuleNotFoundError: No module named 'gpaw.bz_tools'
e>
 at line 2193
[x069.nifl.fysik.dtu.dk:08806] PMIX ERROR: UNREACHABLE in file server/pmix_server.c at line 2193
[x069.nifl.fysik.dtu.dk:08806] PMIX ERROR: UNREACHABLE in file server/pmix_server.c at line 2193
[x069.nifl.fysik.dtu.dk:08806] PMIX ERROR: UNREACHABLE in file server/pmix_server.c at line 2193
[x069.nifl.fysik.dtu.dk:08806] 47 more processes have sent help message help-mpi-api.txt / mpi-abort
[x069.nifl.fysik.dtu.dk:08806] Set MCA parameter "orte_base_help_aggregate" to 0 to see all help / error messages
"""
a, b = parse_stderr(txt)
print(a, b)
