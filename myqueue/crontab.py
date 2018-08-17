import subprocess


def install_crontab_job():
    p = subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE)
    crontab = p.stdout
    cmd = b'bash -lc "python3 -m myqueue kick >> ~/.myqueue/kick.log"'
    if cmd in crontab:
        raise ValueError('Already installed!')
    crontab += b'\n0,30 * * * * ' + cmd + b'\n'
    p = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
    p.communicate(crontab)
