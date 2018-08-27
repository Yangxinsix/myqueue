import subprocess


def install_crontab_job(dry_run: bool) -> None:
    cmd = b'bash -lc "python3 -m myqueue kick >> ~/.myqueue/kick.log"'

    if dry_run:
        print('0,30 * * * *', cmd.decode())
        return

    p1 = subprocess.run(['crontab', '-l'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    crontab = p1.stdout

    if b'myqueue kick' in crontab:
        from myqueue.cli import MyQueueCLIError
        raise MyQueueCLIError('Already installed!')

    crontab += b'\n0,30 * * * * ' + cmd + b'\n'
    p2 = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
    p2.communicate(crontab)
    print('Installed crontab:\n', crontab.decode())
