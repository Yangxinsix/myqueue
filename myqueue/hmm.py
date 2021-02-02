from pathlib import Path


def x(script, name):
    import sys
    from myqueue.workflow import run_workflow_function
    print(script, name, file=sys.stderr)
    run_workflow_function(Path(script), name)
