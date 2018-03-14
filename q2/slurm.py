import os
from pathlib import Path
import subprocess
from typing import List

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

        cores = job.cores[0]
        for size in [24, 16, 8]:
            if cores % size == 0:
                nodes = cores // size
                break
        else:
            if job.cores == 1:
                size = 8
                nodes = 1
            else:
                1 / 0

        cmd = ['sbatch',
               '--partition=xeon{}'.format(size),
               '--job-name={}'.format(job.name),
               '--time={}'.format(job.time // 60),
               '--njobs={}'.format(cores),
               '--nodes={}'.format(nodes),
               '--output={}.out'.format(job.name),
               '--error={}.err'.format(job.name)]

        if job.deps:
            ids = ':'.join(str(dep.id) for dep in job.deps)
            cmd.append('--dependency=afterok:{}'.format(ids))

        mpicmd = 'mpirun'
        if size == 24:
            mpicmd += ' -mca pml cm -mca mtl psm2 -x OMP_NUM_THREADS=1'
        mpicmd += str(job.cmd).replace('python3', 'gpaw-python')

        msg = 'python3 -m q2.jobs'
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0
        job.state = 'running'
        script = ('#!/bin/bash -l\n'
                  'id=$SLURM_JOB_ID\n'
                  '({msg} $id running && '
                  '{mpi} && {msg} $id done) || {msg} $id FAILED\n'
                  .format(mpi=mpicmd, msg=msg))

        p = subprocess.Popen(cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(script.encode())
        assert p.returncode == 0
        id = int(out.split()[-1])
        job.id = id

    def timeout(self, name, id):
        err = Path('slurm-{}-{}.err'.format(name, id))
        if err.is_file():
            with open(str(err)) as f:
                for line in f:
                    if line.endswith('DUE TO TIME LIMIT ***\n'):
                        return True
        return False

    def cancel(self, ids):
        subprocess.run(['scancel'] + [str[id] for id in ids])

    def jobs(self):
        user = os.environ['USER']
        cmd = ['squeue', '--user', user]
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE)
        except FileNotFoundError:
            cmd[:0] = ['ssh', os.environ.get('SLURM_FRONTEND', 'sylg')]
            p = subprocess.run(cmd, stdout=subprocess.PIPE)
        queued = {int(line.split()[0]) for line in p.stdout.splitlines()[1:]}
        return queued
