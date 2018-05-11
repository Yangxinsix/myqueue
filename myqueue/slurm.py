import subprocess
from math import ceil
from typing import List

from myqueue.job import Job
from myqueue.runner import Runner


class SLURM(Runner):
    def __init__(self):
        cfg = read_config
        self.nodes = OrderedDict((node, spec) for node, spec in nodelist)

    def submit(self, jobs: List[Job]) -> None:
        for job in jobs:
            self.submit1([job])

    def submit1(self, job: Job) -> None:
        nodes, nodename, processes = job.resources.select(self.nodes)
        nodedct = self.nodes[nodename]

        name = job.cmd.name
        sbatch = ['sbatch',
                  '--patition={}'.format(nodename),
                  '--job-name={}'.format(name),
                  '--time={}'.format(ceil(job.tmax / 60)),
                  '--ntasks={}'.format(processes),
                  '--nodes={}'.format(nodes),
                  '--workdir={}'.format(job.folder.expanduser()),
                  '--output={}.%j.out'.format(name),
                  '--error={}.%j.err'.format(name)]

        mem = nodedct.get('memory')
        if mem:
            sbatch.append('--mem={}'.format(mem))

        if job.deps:
            ids = ':'.join(str(dep.id) for dep in job.deps)
            sbatch.append('--dependency=afterok:{}'.format(ids))

        cmd = str(job.cmd)
        if job.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 -x MPLBACKEND=Agg '
            if 'mpiargs' in nodedct:
                mpiexec += nodedct['mpiargs'] + ' '
            cmd = mpiexec + cmd.replace('python3', self.parallel_python)
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
        job.id = id

    def timeout(self, job):
        path = (job.folder /
                '{}.{}.err'.format(job.cmd.name, job.id)).expanduser()
        if path.is_file():
            job.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines:
                if line.endswith('DUE TO TIME LIMIT ***'):
                    return True
        return False

    def cancel(self, job):
        subprocess.run(['scancel', str(job.id)])
