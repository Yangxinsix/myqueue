import subprocess

from myqueue.cli import MQError


def install_crontab_job(dry_run: bool) -> None:
    kick = 'python3 -m myqueue kick --all >> ~/.myqueue/kick.log'
    cmd = f'bash -lc "{kick}"'

    if dry_run:
        print('0,30 * * * *', cmd)
        return

    p1 = subprocess.run(['crontab', '-l'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    crontab = p1.stdout.decode()

    if 'myqueue kick' in crontab:
        raise MQError('Already installed!')

    crontab += '\n0,30 * * * * ' + cmd + '\n'
    p2 = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
    p2.communicate(crontab.encode())
    print('Installed crontab:\n', crontab)
