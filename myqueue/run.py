import subprocess


def run_tasks(tasks):
    for task in tasks:
        cmd = str(task.cmd)
        print(f'{task.folder}: {cmd}')
        cmd = 'MPLBACKEND=Agg ' + cmd
        cmd = f'cd {task.folder} && {cmd}'
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0


def run(tasks):
    pass

    # import mp
    # mp.pool(run1)


def run1(task):
    pass
    # os.chdir(task.folder)
    # with contextlib.redirect_stdout(out):
    #     ...
