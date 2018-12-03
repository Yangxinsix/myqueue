import os
import subprocess

from myqueue.task import Task
from myqueue.config import config
from myqueue.queue import Queue


class PBS(Queue):
    def submit(self, task: Task) -> None:
        nodelist = config['nodes']
        nodes, nodename, nodedct = task.resources.select(nodelist)

        name = task.cmd.name
        processes = task.resources.processes

        if processes < nodedct['cores']:
            ppn = processes
        else:
            assert processes % nodes == 0
            ppn = processes // nodes

        hours, rest = divmod(task.resources.tmax, 3600)
        minutes, seconds = divmod(rest, 60)

        qsub = ['qsub',
                '-N',
                name,
                '-l',
                'walltime={}:{:02}:{:02}'.format(hours, minutes, seconds),
                '-l',
                'nodes={nodes}:ppn={ppn}' .format(nodes=nodes, ppn=ppn),
                '-d', str(task.folder)]

        qsub += nodedct.get('extra_args', [])

        if task.dtasks:
            ids = ':'.join(str(tsk.id) for tsk in task.dtasks)
            qsub.extend(['-W', 'depend=afterok:{}'.format(ids)])

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 -x MPLBACKEND=Agg '
            if 'mpiargs' in nodedct:
                mpiexec += nodedct['mpiargs'] + ' '
            cmd = mpiexec + cmd.replace('python3', config['parallel_python'])
        else:
            cmd = 'MPLBACKEND=Agg ' + cmd

        home = config['home']

        script = (
            '#!/bin/bash -l\n'
            'id=${{PBS_JOBID%.*}}\n'
            'mq={home}/.myqueue/pbs-$id\n'
            '(touch $mq-0 && cd {dir} && {cmd} && touch $mq-1) || '
            'touch $mq-2\n'
            .format(home=home, dir=task.folder, cmd=cmd))

        p = subprocess.Popen(qsub,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(script.encode())
        assert p.returncode == 0
        id = int(out.split(b'.')[0])
        task.id = id

    def timeout(self, task):
        path = (task.folder /
                '{}.e{}'.format(task.cmd.name, task.id)).expanduser()
        if path.is_file():
            task.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines:
                if line.endswith('DUE TO TIME LIMIT ***'):
                    return True
        return False

    def cancel(self, task):
        subprocess.run(['qdel', str(task.id)])

    def get_ids(self):
        user = os.environ['USER']
        cmd = ['qstat', '-u', user]
        host = config.get('host')
        if host:
            cmd[:0] = ['ssh', host]
        p = subprocess.run(cmd, stdout=subprocess.PIPE)
        queued = {int(line.split()[0].split(b'.')[0])
                  for line in p.stdout.splitlines()
                  if line[:1].isdigit()}
        return queued
