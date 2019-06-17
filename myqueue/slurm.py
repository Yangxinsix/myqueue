import os
import subprocess
from math import ceil
from typing import Set

from myqueue.task import Task
from myqueue.config import config
from myqueue.queue import Queue


def mpi_implementation() -> str:
    if 'mpi' in config:
        return config['mpi']
    mpiexec = config.get('mpiexec', 'mpiexec')
    if b'intel' in subprocess.check_output([mpiexec, '-V']).lower():
        return 'intel'
    return 'openmpi'


class SLURM(Queue):
    def submit(self, task: Task) -> None:
        nodelist = config['nodes']
        nodes, nodename, nodedct = task.resources.select(nodelist)

        name = task.cmd.name
        sbatch = ['sbatch',
                  '--partition={}'.format(nodename),
                  '--job-name={}'.format(name),
                  '--time={}'.format(ceil(task.resources.tmax / 60)),
                  '--ntasks={}'.format(task.resources.processes),
                  '--nodes={}'.format(nodes),
                  '--workdir={}'.format(task.folder),
                  '--output={}.%j.out'.format(name),
                  '--error={}.%j.err'.format(name)]

        mem = nodedct.get('memory')
        if mem:
            assert mem[-1] == 'G'
            mbytes = 1000 * int(mem[:-1])
            cores = task.resources.cores
            if nodes == 1 and cores < nodedct['cores']:
                mbytes = int(mbytes * cores / nodedct['cores'])
            sbatch.append(f'--mem={mbytes}M')

        features = nodedct.get('features')
        if features:
            sbatch.append(f'--constraint={features}')

        reservation = nodedct.get('reservation')
        if reservation:
            sbatch.append(f'--reservation={reservation}')

        if task.dtasks:
            ids = ':'.join(str(tsk.id) for tsk in task.dtasks)
            sbatch.append('--dependency=afterok:{}'.format(ids))

        env = [('OMP_NUM_THREADS', '1'),
               ('MPLBACKEND', 'Agg')]

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = config.get('mpiexec', 'mpiexec')
            if mpi_implementation() == 'intel':
                mpiexec += ' ' + ' '.join(f'--env {name} {val}'
                                          for name, val in env)
            else:
                mpiexec += ' ' + ' '.join(f'-x {name}={val}'
                                          for name, val in env)
            if 'mpiargs' in nodedct:
                mpiexec += ' ' + nodedct['mpiargs']
            cmd = (mpiexec +
                   ' ' +
                   cmd.replace('python3',
                               config.get('parallel_python', 'python3')))
        else:
            cmd = ''.join(f'{name}={val} ' for name, val in env) + cmd

        home = config['home']

        script = (
            '#!/bin/bash -l\n'
            'id=$SLURM_JOB_ID\n'
            'mq={home}/.myqueue/slurm-$id\n'
            '(touch $mq-0 && cd {dir} && {cmd} && touch $mq-1) || '
            '(touch $mq-2; exit 1)\n'
            .format(home=home, dir=task.folder, cmd=cmd))

        p = subprocess.Popen(sbatch,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(script.encode())

        assert p.returncode == 0
        id = int(out.split()[-1])
        task.id = id

    def timeout(self, task: Task) -> bool:
        path = (task.folder /
                '{}.{}.err'.format(task.cmd.name, task.id)).expanduser()
        if path.is_file():
            task.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines:
                if line.endswith('DUE TO TIME LIMIT ***'):
                    return True
        return False

    def cancel(self, task: Task) -> None:
        subprocess.run(['scancel', str(task.id)])

    def hold(self, task: Task) -> None:
        subprocess.run(['scontrol', 'hold', str(task.id)])

    def release_hold(self, task: Task) -> None:
        subprocess.run(['scontrol', 'release', str(task.id)])

    def get_ids(self) -> Set[int]:
        user = os.environ['USER']
        cmd = ['squeue', '--user', user]
        host = config.get('host')
        if host:
            cmd[:0] = ['ssh', host]
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        queued = {int(line.split()[0]) for line in p.stdout.splitlines()[1:]}
        return queued
