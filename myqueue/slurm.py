import subprocess
from typing import List

from myqueue.config import read_config
from myqueue.job import Job
from myqueue.runner import Runner


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
            size = 8
            nodes = job.cores // 8 + 1

        name = job.cmd.name
        sbatch = ['sbatch',
                  '--partition=xeon{}'.format(size),
                  '--job-name={}'.format(name),
                  '--time={}'.format(max(job.tmax // 60, 1)),
                  '--ntasks={}'.format(job.processes),
                  '--nodes={}'.format(nodes),
                  '--workdir={}'.format(job.folder.expanduser()),
                  '--output={}.%j.out'.format(name),
                  '--error={}.%j.err'.format(name),
                  '--mem=0']

        cfg = read_config()
        sbatch += cfg.get('slurm', {}).get('extra', [])

        if job.deps:
            ids = ':'.join(str(dep.id) for dep in job.deps)
            sbatch.append('--dependency=afterok:{}'.format(ids))

        cmd = str(job.cmd)
        if job.processes > 1:
            mpirun = 'mpirun '
            if size == 24:
                mpirun += '-mca pml cm -mca mtl psm2 -x OMP_NUM_THREADS=1 '
            cmd = mpirun + cmd.replace('python3', 'gpaw-python')

        script = ('#!/bin/bash -l\n'
                  'id=$SLURM_JOB_ID\n'
                  'msg="python3 -m myqueue.queue slurm $id"\n'
                  '($msg running && {cmd} && $msg done) || $msg FAILED\n'
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
