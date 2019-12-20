import subprocess
from pathlib import Path
from typing import Optional, Set

from .task import Task
from .config import config
from .scheduler import Scheduler


class LSF(Scheduler):
    def submit(self,
               task: Task,
               activation_script: Optional[Path] = None,
               dry_run: bool = False) -> None:
        nodelist = config['nodes']
        nodes, nodename, nodedct = task.resources.select(nodelist)

        name = task.cmd.short_name
        hours, minutes = divmod(max(task.resources.tmax, 60) // 60, 60)

        bsub = ['bsub',
                '-J', name,
                '-W', f'{hours:02}:{minutes:02}',
                '-n', str(task.resources.cores),
                '-o', f'{name}.%J.out',
                '-e', f'{name}.%J.err']

        mem = nodedct['memory']
        assert mem[-1] == 'G'
        gbytes = int(mem[:-1]) // nodedct['cores']
        bsub += ['-R', f'rusage[mem={gbytes}G]']

        if task.dtasks:
            ids = ' && '.join(f'done({t.id})'
                              for t in task.dtasks)
            bsub += ['-w', f'"{ids}"']

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            cmd = ('mpiexec ' +
                   cmd.replace('python3',
                               config.get('parallel_python', 'python3')))

        home = config['home']

        script = (
            '#!/bin/bash -l\n'
            'id=$LSB_JOBID\n'
            f'mq={home}/.myqueue/lsf-$id\n')

        if activation_script:
            script += (
                f'source {activation_script}\n'
                f'echo "venv: {activation_script}"\n')

        script += (
            '(touch $mq-0 && \\\n'
            f' cd {str(task.folder)!r} && \\\n'
            f' {cmd} && \\\n'
            ' touch $mq-1) || \\\n'
            '(touch $mq-2; exit 1)\n')

        if dry_run:
            print(' \\\n    '.join(bsub))
            print(script)
            return

        p = subprocess.Popen(bsub,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(script.encode())

        assert p.returncode == 0
        id = int(out.split()[1][1:-1])
        task.id = id

    def has_timed_out(self, task: Task) -> bool:
        path = self.error_file(task).expanduser()
        if path.is_file():
            task.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines:
                if line.startswith('TERM_RUNLIMIT:'):
                    return True
        return False

    def cancel(self, task: Task) -> None:
        subprocess.run(['bkill', str(task.id)])

    def get_ids(self) -> Set[int]:
        p = subprocess.run(['bjobs'], stdout=subprocess.PIPE)
        queued = {int(line.split()[0])
                  for line in p.stdout.splitlines()
                  if line[:1].isdigit()}
        return queued
