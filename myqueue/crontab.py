import subprocess


def install_crontab_job():
    p = subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE)
    crontab = p.stdout
    cmd = b'python3 -m myqueue kick'
    if cmd in crontab:
        raise ValueError('Already installed!')
    crontab += b'\n0,10,20,30,40,50 * * * * ' + cmd + b'\n'
    p = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE)
    p.communicate(crontab)
