from __future__ import annotations
import os
import subprocess
from math import ceil

from myqueue.task import Task
from myqueue.schedulers import Scheduler, SchedulerError


class SLURM(Scheduler):
    def submit(self,
               task: Task,
               dry_run: bool = False,
               verbose: bool = False) -> int:
        nodelist = self.config.nodes
        nodes, nodename, nodedct = task.resources.select(nodelist)

        name = task.cmd.short_name
        sbatch = ['sbatch',
                  f'--partition={nodename}',
                  f'--job-name={name}',
                  f'--time={ceil(task.resources.tmax / 60)}',
                  f'--ntasks={task.resources.cores}',
                  f'--nodes={nodes}',
                  f'--chdir={task.folder}',
                  f'--output={name}.%j.out',
                  f'--error={name}.%j.err']

        extra_args = self.config.extra_args + nodedct.get('extra_args', [])
        sbatch += extra_args

        if task.dtasks:
            ids = ':'.join(str(tsk.id) for tsk in task.dtasks)
            sbatch.append(f'--dependency=afterok:{ids}')

        env = []

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            if 'OMP_NUM_THREADS' not in os.environ:
                env.append(('OMP_NUM_THREADS', '1'))
            mpiexec = self.config.mpiexec
            if 'mpiargs' in nodedct:
                mpiexec += ' ' + nodedct['mpiargs']
            cmd = mpiexec + ' ' + cmd.replace('python3',
                                              self.config.parallel_python)

        # Use bash for the script
        script = '#!/bin/bash -l\n'

        # Add environment variables
        if len(env) > 0:
            script += '\n'.join(f'export {name}={val}' for name, val in env)
            script += '\n'

        home = self.config.home
        script += (
            'id=$SLURM_JOB_ID\n'
            f'mq={home}/.myqueue/slurm-$id\n')

        script += self.get_venv_activation_line()

        script += (
            '(touch $mq-0 && \\\n'
            f' cd {str(task.folder)!r} && \\\n'
            f' {cmd} && \\\n'
            ' touch $mq-1) || \\\n'
            '(touch $mq-2; exit 1)\n')

        if dry_run:
            if verbose:
                print(' \\\n    '.join(sbatch))
                print(script)
            return 1

        # Use a clean set of environment variables without any MPI stuff:
        p = subprocess.run(sbatch,
                           input=script.encode(),
                           capture_output=True,
                           env=os.environ)

        if p.returncode:
            raise SchedulerError((p.stderr + p.stdout).decode())

        return int(p.stdout.split()[-1].decode())

    def cancel(self, id: int) -> None:
        subprocess.run(['scancel', str(id)])

    def hold(self, id: int) -> None:
        subprocess.run(['scontrol', 'hold', str(id)])

    def release_hold(self, id: int) -> None:
        subprocess.run(['scontrol', 'release', str(id)])

    def get_ids(self) -> set[int]:
        user = os.environ.get('USER', 'test')
        cmd = ['squeue', '--user', user]
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        queued = {int(line.split()[0].decode())
                  for line in p.stdout.splitlines()[1:]}
        return queued

    def maxrss(self, id: int) -> int:
        cmd = ['sacct',
               '-j', str(id),
               '-n',
               '--units=K',
               '-o', 'MaxRSS']
        try:
            p = subprocess.run(cmd, stdout=subprocess.PIPE)
        except FileNotFoundError:
            return 0
        mem = 0
        for line in p.stdout.splitlines():
            line = line.strip()
            if line.endswith(b'K'):
                mem = max(mem, int(line[:-1]) * 1000)
        return mem

    def get_config(self, queue: str = '') -> tuple[list[tuple[str, int, str]],
                                                   list[str]]:
        cmd = ['sinfo',
               '--noheader',
               '-O',
               'CPUs,Memory,Partition']
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        nodes = []
        for line in p.stdout.decode().splitlines():
            cores, mem, name = line.split()
            nodes.append((name.rstrip('*'),
                          int(cores),
                          mem.rstrip('+') + 'M'))
        return nodes, []
