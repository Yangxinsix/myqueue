import subprocess

kick = """\
for d in `cat ~/.myqueue/folders.txt`
do cd $d; python3 -m myqueue kick
done >> ~/.myqueue/kick.log"""


def install_crontab_job(dry_run: bool) -> None:
    cmd = 'bash -lc "{}"'.format(kick.replace('\n', '; '))

    if dry_run:
        print('0,30 * * * *', cmd)
        return

    p1 = subprocess.run(['crontab', '-l'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    crontab = p1.stdout.decode()

    if 'myqueue kick' in crontab:
        from myqueue.cli import MyQueueCLIError
        raise MyQueueCLIError('Already installed!')

    crontab += '\n0,30 * * * * ' + cmd + '\n'
    p2 = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
    p2.communicate(crontab.encode())
    print('Installed crontab:\n', crontab)
