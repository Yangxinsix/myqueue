import os
import subprocess
import warnings
from math import ceil
from typing import Set, List, Tuple

from .task import Task
from .scheduler import Scheduler
from .utils import str2number


class SLURM(Scheduler):
    def submit(self,
               task: Task,
               dry_run: bool = False,
               verbose: bool = False) -> None:
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

        mem = nodedct.get('memory')
        if mem:
            mbytes = str2number(mem) // 1_000_000
            cores = task.resources.cores
            if nodes == 1 and cores < nodedct['cores']:
                mbytes = int(mbytes * cores / nodedct['cores'])
            sbatch.append(f'--mem={mbytes}MB')

        extra_args = self.config.extra_args + nodedct.get('extra_args', [])
        if extra_args:
            sbatch += extra_args

        features = nodedct.get('features')
        if features:
            warnings.warn('Please use extra_args instead of features!')
            sbatch.append(f'--constraint={features}')

        reservation = nodedct.get('reservation')
        if reservation:
            warnings.warn('Please use extra_args instead of reservation!')
            sbatch.append(f'--reservation={reservation}')

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

        if task.activation_script:
            script += (
                f'source {task.activation_script}\n'
                f'echo "venv: {task.activation_script}"\n')

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
            task.id = 1
            return

        # Use a clean set of environment variables without any MPI stuff:
        p = subprocess.Popen(sbatch,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             env=os.environ)
        out, err = p.communicate(script.encode())

        if p.returncode != 0:
            raise RuntimeError(err)

        task.id = int(out.split()[-1])

    def cancel(self, task: Task) -> None:
        subprocess.run(['scancel', str(task.id)])

    def hold(self, task: Task) -> None:
        subprocess.run(['scontrol', 'hold', str(task.id)])

    def release_hold(self, task: Task) -> None:
        subprocess.run(['scontrol', 'release', str(task.id)])

    def get_ids(self) -> Set[int]:
        user = os.environ['USER']
        cmd = ['squeue', '--user', user]
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        queued = {int(line.split()[0]) for line in p.stdout.splitlines()[1:]}
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

    def get_config(self, queue: str = '') -> Tuple[List[Tuple[str, int, str]],
                                                   List[str]]:
        cmd = ['sinfo',
               '--noheader',
               '--format=%c %m %P']
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        nodes = []
        for line in p.stdout.decode().splitlines():
            cores, mem, name = line.split()
            nodes.append((name.rstrip('*'),
                          int(cores),
                          mem.rstrip('+') + 'M'))
        return nodes, []
