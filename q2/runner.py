class Runner:
    pass


def get_runner(name: str) -> Runner:
    if 'local'.startswith(name):
        from q2.local import LocalRunner
        return LocalRunner()
    if 'slurm'.startswith(name):
        from q2.sluirml import SLURMRunner
        return SLURMRunner()
    else:
        1 / 0
