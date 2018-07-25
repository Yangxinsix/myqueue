import os
import subprocess
from math import ceil

from myqueue.task import Task
from myqueue.config import read_config, home_folder
from myqueue.queue import Queue


class PBS(Queue):
    def __init__(self):
        self.cfg = read_config()

    def submit(self, task: Task) -> None:
        nodelist = self.cfg['nodes']
        nodes, nodename, nodedct = task.resources.select(nodelist)

        name = task.cmd.name
        processes = task.resources.processes

        if processes < nodedct['cores']:
            ppn = processes
        else:
            assert processes % nodes == 0
            ppn = processes // nodes

        sbatch = ['qsub',
                  '-N',
                  name,
                  '-l',
                  'walltime={}:00:00'.format(ceil(task.resources.tmax / 60)),
                  '-l',
                  'nodes={nodes}:ppn={ppn}'
                  .format(node=nodes, ppn=ppn)]

        if task.dtasks:
            ids = ':'.join(str(tsk.id) for tsk in task.dtasks)
            sbatch.extend(['-W', 'afterok:{}'.format(ids)])

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 -x MPLBACKEND=Agg '
            if 'mpiargs' in nodedct:
                mpiexec += nodedct['mpiargs'] + ' '
            cmd = mpiexec + cmd.replace('python3', self.cfg['parallel_python'])
        else:
            cmd = 'MPLBACKEND=Agg ' + cmd

        home = home_folder()

        script = (
            '#!/bin/bash -l\n'
            'id=$SLURM_JOB_ID\n'
            'mq={home}/slurm-$id\n'
            '(touch $mq-0 && cd {dir} && {cmd} && touch $mq-1) || '
            'touch $mq-2\n'
            .format(home=home, dir=task.folder, cmd=cmd))

        p = subprocess.Popen(sbatch,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(script.encode())
        assert p.returncode == 0
        id = int(out.split()[-1])
        task.id = id

    def timeout(self, task):
        path = (task.folder /
                '{}.{}.err'.format(task.cmd.name, task.id)).expanduser()
        if path.is_file():
            task.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines:
                if line.endswith('DUE TO TIME LIMIT ***'):
                    return True
        return False

    def cancel(self, task):
        subprocess.run(['qdel', str(task.id)])

    def get_ids(self):
        user = os.environ['USER']
        cmd = ['squeue', '--user', user]
        host = self.cfg.get('host')
        if host:
            cmd[:0] = ['ssh', host]
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        queued = {int(line.split()[0]) for line in p.stdout.splitlines()[1:]}
        return queued
