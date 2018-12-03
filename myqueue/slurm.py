import os
import subprocess
from math import ceil
from typing import Set

from myqueue.task import Task
from myqueue.config import config
from myqueue.queue import Queue


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
            sbatch.append('--mem={mbytes}M'.format(mbytes=mbytes))

        features = nodedct.get('features')
        if features:
            sbatch.append('--constraint={}'.format(features))

        if task.dtasks:
            ids = ':'.join(str(tsk.id) for tsk in task.dtasks)
            sbatch.append('--dependency=afterok:{}'.format(ids))

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 -x MPLBACKEND=Agg '
            if config.get('mpi') == 'intel':
                mpiexec = mpiexec.replace('-x', '--env').replace('=', ' ')
            if 'mpiargs' in nodedct:
                mpiexec += nodedct['mpiargs'] + ' '
            cmd = mpiexec + cmd.replace('python3', config['parallel_python'])
        else:
            cmd = 'MPLBACKEND=Agg ' + cmd

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

        # print(script.encode(), sbatch)

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
