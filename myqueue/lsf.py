import subprocess
from typing import Set, List, Tuple, Dict

from .task import Task
from .config import config
from .scheduler import Scheduler
from .utils import str2number


class LSF(Scheduler):
    def submit(self,
               task: Task,
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
                '-e', f'{name}.%J.err',
                '-R', f'select[model == {nodename}]']

        mem = nodedct['memory']
        gbytes = int(str2number(mem) / 1_000_000_000 / nodedct['cores'])
        bsub += ['-R', f'rusage[mem={gbytes}G]']

        extra_args = (config.get('extra_args', []) +
                      nodedct.get('extra_args', []))
        if extra_args:
            bsub += extra_args

        if task.dtasks:
            ids = ' && '.join(f'done({t.id})'
                              for t in task.dtasks)
            bsub += ['-w', f'"{ids}"']

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            bsub += ['-R', f'span[hosts={nodes}]']
            cmd = ('mpiexec ' +
                   cmd.replace('python3',
                               config.get('parallel_python', 'python3')))

        home = config['home']

        script = (
            '#!/bin/bash -l\n'
            'id=$LSB_JOBID\n'
            f'mq={home}/.myqueue/lsf-$id\n')

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

    def get_config(self) -> List[Tuple[str, int, str]]:
        from collections import defaultdict
        from .utils import str2number

        cmd = ['nodestat',
               '-F']
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        cores: Dict[str, int] = {}
        memory: Dict[str, List[str]] = defaultdict(list)
        for line in p.stdout.decode().splitlines():
            id, state, procs, load, name, mem, unit, *_ = line.split()
            if state == 'State':
                continue  # skip header
            if state == 'Down':
                continue
            cores[name] = int(procs.split(':')[1])
            memory[name].append(mem + unit)
        nodes = [
            (name, cores[name], min(memory[name], key=str2number))
            for name in cores]
        return nodes
