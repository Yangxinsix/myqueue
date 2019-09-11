import subprocess


def run_tasks(tasks):
    for task in tasks:
        cmd = str(task.cmd)
        print(f'{task.folder}: {cmd}')
        cmd = 'MPLBACKEND=Agg ' + cmd
        cmd = f'cd {task.folder} && {cmd}'
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0
