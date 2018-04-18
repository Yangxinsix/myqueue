import subprocess
from typing import List

from q2.config import read_config
from q2.job import Job
from q2.runner import Runner


class SLURM(Runner):
    def submit(self, jobs: List[Job]) -> None:
        if len(jobs) != 1:
            for job in jobs:
                self.submit([job])
            return

        # Submit one job:
        job = jobs[0]

        for size in [24, 16, 8]:
            if job.cores % size == 0:
                nodes = job.cores // size
                break
        else:
            if job.cores < 8:
                size = 8
                nodes = 1
            else:
                raise ValueError('...')

        name = job.cmd.name
        cmd = ['sbatch',
               '--partition=xeon{}'.format(size),
               '--job-name={}'.format(name),
               '--time={}'.format(max(job.tmax // 60, 1)),
               '--ntasks={}'.format(job.cores),
               '--nodes={}'.format(nodes),
               '--workdir={}'.format(job.folder.expanduser()),
               '--output={}.%j.out'.format(name),
               '--error={}.%j.err'.format(name),
               '--mem=0']

        cfg = read_config()
        cmd += cfg.get('slurm', {}).get('extra', [])

        if job.deps:
            ids = ':'.join(str(dep.id) for dep in job.deps)
            cmd.append('--dependency=afterok:{}'.format(ids))

        mpicmd = 'mpirun '
        if size == 24:
            mpicmd += '-mca pml cm -mca mtl psm2 -x OMP_NUM_THREADS=1 '
        mpicmd += str(job.cmd).replace('python3', 'gpaw-python')

        script = ('#!/bin/bash -l\n'
                  'id=$SLURM_JOB_ID\n'
                  'msg="python3 -m q2.queue slurm $id"\n'
                  '($msg running && {mpi} && $msg done) || $msg FAILED\n'
                  .format(mpi=mpicmd))

        p = subprocess.Popen(cmd,
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
