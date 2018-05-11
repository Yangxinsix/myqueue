import subprocess
from math import ceil

from myqueue.task import Task
from myqueue.config import read_config
from myqueue.queue import Queue


class SLURM(Queue):
    def __init__(self, name):
        Queue.__init__(self, name)
        self.cfg = read_config()[name]

    def submit(self, task: Task) -> None:
        nodelist = self.cfg['nodes']
        nodes, nodename, nodedct = task.resources.select(nodelist)

        name = task.cmd.name
        sbatch = ['sbatch',
                  '--patition={}'.format(nodename),
                  '--task-name={}'.format(name),
                  '--time={}'.format(ceil(task.tmax / 60)),
                  '--ntasks={}'.format(task.resources.processes),
                  '--nodes={}'.format(nodes),
                  '--workdir={}'.format(task.folder),
                  '--output={}.%j.out'.format(name),
                  '--error={}.%j.err'.format(name)]

        mem = nodedct.get('memory')
        if mem:
            sbatch.append('--mem={}'.format(mem))

        if task.deps:
            ids = ':'.join(str(dep.id) for dep in task.deps)
            sbatch.append('--dependency=afterok:{}'.format(ids))

        cmd = str(task.cmd)
        if task.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 -x MPLBACKEND=Agg '
            if 'mpiargs' in nodedct:
                mpiexec += nodedct['mpiargs'] + ' '
            cmd = mpiexec + cmd.replace('python3', self.cfg['parallel_python'])
        else:
            cmd = 'MPLBACKEND=Agg ' + cmd

        script = (
            '#!/bin/bash -l\n'
            'id=$SLURM_JOB_ID\n'
            'mq=~/.myqueue/slurm-$id\n'
            '(touch $mq-0 && {cmd} && touch $mq-1) || touch $mq-2\n'
            .format(cmd=cmd))

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
        subprocess.run(['scancel', str(task.id)])
