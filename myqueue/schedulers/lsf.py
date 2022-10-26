from __future__ import annotations
import subprocess

from myqueue.task import Task
from myqueue.schedulers import Scheduler, SchedulerError
from myqueue.utils import str2number


class LSF(Scheduler):
    def submit(self,
               task: Task,
               dry_run: bool = False,
               verbose: bool = False) -> int:
        nodelist = self.config.nodes
        nodes, nodename, nodedct = task.resources.select(nodelist)

        name = task.cmd.short_name
        hours, minutes = divmod(max(task.resources.tmax, 60) // 60, 60)

        bsub = ['bsub',
                '-J', name,
                '-W', f'{hours:02}:{minutes:02}',
                '-n', str(task.resources.cores),
                '-o', f'{task.folder}/{name}.%J.out',
                '-e', f'{task.folder}/{name}.%J.err',
                '-R', f'select[model == {nodename}]']

        mem = nodedct['memory']
        gbytes = int(str2number(mem) / 1_000_000_000 / nodedct['cores'])
        bsub += ['-R', f'rusage[mem={gbytes}G]']

        extra_args = self.config.extra_args + nodedct.get('extra_args', [])
        if extra_args:
            bsub += extra_args

        if task.dtasks:
            ids = ' && '.join(f'done({t.id})'
                              for t in task.dtasks)
            bsub += ['-w', f"{ids}"]

        # bsub += ['-R', f'span[hosts={nodes}]']
        bsub += ['-R', 'span[hosts=1]']

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            cmd = 'mpiexec ' + cmd.replace('python3',
                                           self.config.parallel_python)

        home = self.config.home

        script = (
            '#!/bin/bash -l\n'
            'id=$LSB_JOBID\n'
            f'mq={home}/.myqueue/lsf-$id\n')

        script += self.get_venv_activation_line()

        script += (
            '(touch $mq-0 && \\\n'
            f' cd {str(task.folder)!r} && \\\n'
            f' {cmd} && \\\n'
            ' touch $mq-1) || \\\n'
            '(touch $mq-2; exit 1)\n')

        # print(' \\\n    '.join(bsub))
        # print(script)
        if dry_run:
            print(' \\\n    '.join(bsub))
            print(script)
            return 1

        p = subprocess.run(bsub,
                           input=script.encode(),
                           capture_output=True)
        if p.returncode:
            raise SchedulerError((p.stderr + p.stdout).decode())
        id = int(p.stdout.split()[1][1:-1].decode())
        return id

    def has_timed_out(self, task: Task) -> bool:
        path = self.error_file(task).expanduser()
        if path.is_file():
            task.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines:
                if line.startswith('TERM_RUNLIMIT:'):
                    return True
        return False

    def cancel(self, id: int) -> None:
        subprocess.run(['bkill', str(id)])

    def get_ids(self) -> set[int]:
        p = subprocess.run(['bjobs'], stdout=subprocess.PIPE)
        queued = {int(line.split()[0].decode())
                  for line in p.stdout.splitlines()
                  if line[:1].isdigit()}
        return queued

    def get_config(self, queue: str = '') -> tuple[list[tuple[str, int, str]],
                                                   list[str]]:
        from collections import defaultdict

        cmd = ['nodestat', '-F', queue]
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        cores: dict[str, int] = {}
        memory: dict[str, list[str]] = defaultdict(list)
        for line in p.stdout.decode().splitlines():
            _, state, procs, _, name, mem, unit, *_ = line.split()
            if state == 'State':
                continue  # skip header
            if state == 'Down':
                continue
            cores[name] = int(procs.split(':')[1])
            memory[name].append(mem + unit)
        nodes = [
            (name, n, min(memory[name], key=str2number))
            for name, n in cores.items()]
        if queue:
            extra_args = ['-q', queue]
        else:
            extra_args = []
        return nodes, extra_args
