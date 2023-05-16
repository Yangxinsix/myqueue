from myqueue.errors import parse_stderr

txt = """
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


def test_niflheim_error():
    err, oom = parse_stderr(txt)
    assert not oom
    assert err == "L17: ModuleNotFoundError: No module named 'gpaw.bz_tools'"
