import os
from pathlib import Path
import subprocess


class SLURM:
    def __init__(self, dry_run):
        self.dry_run = dry_run

    def submit(self, job, deps):
        for size in [24, 16, 8]:
            if job.cores % size == 0:
                nodes = job.cores // size
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
               '--njobs={}'.format(job.cores),
               '--nodes={}'.format(nodes),
               '--output={}.out'.format(job.name),
               '--error={}.err'.format(job.name)]

        if deps:
            ids = ':'.join(str(dep.jobid) for dep in deps)
            cmd.append('--dependency=afterok:{}'.format(ids))

        mpi = 'mpirun'
        if size == 24:
            mpi += ' -mca pml cm -mca mtl psm2 -x OMP_NUM_THREADS=1'

        args = command(job.module, job.function)

        script = ('#!/bin/bash -l\n'
                  'python3 -m c2dm.jobs clear -s running {name} . && '
                  '{mpi} gpaw-python {args} && '
                  'python3 -m c2dm.jobs clear -s done {name} .\n'
                  .format(mpi=mpi, args=args, name=job.name))

        if self.dry_run:
            return 42

        p = subprocess.Popen(cmd,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(script.encode())
        assert p.returncode == 0
        jobid = int(out.split()[-1])
        return jobid

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
