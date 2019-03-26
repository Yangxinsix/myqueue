import json
import subprocess
import sys

from myqueue.config import config, initialize_config
from myqueue.queue import Queue
from myqueue.task import Task
from myqueue.utils import Lock, lock


class LocalQueue(Queue, Lock):
    def __init__(self):
        self.fname = config['home'] / '.myqueue' / 'local.json'
        Lock.__init__(self, self.fname.with_name('local.json.lock'))
        self.tasks = []
        self.number = None
        Queue.__init__(self)

    @lock
    def submit(self, task: Task) -> None:
        self._read()
        if task.dtasks:
            ids = {t.id for t in self.tasks}
            for t in task.dtasks:
                assert t.id in ids
        self.number += 1
        task.id = self.number
        self.tasks.append(task)
        self._write()

    @lock
    def cancel(self, task):
        assert task.state == 'queued', task
        self._read()
        for i, j in enumerate(self.tasks):
            if task.id == j.id:
                break
        else:
            raise ValueError('No such task!')
        del self.tasks[i]
        self._write()

    @lock
    def hold(self, task):
        assert task.state == 'queued', task
        self._read()
        for i, j in enumerate(self.tasks):
            if task.id == j.id:
                break
        else:
            raise ValueError('No such task!')
        j.state = 'hold'
        self._write()

    @lock
    def release_hold(self, task):
        assert task.state == 'hold', task
        self._read()
        for i, j in enumerate(self.tasks):
            if task.id == j.id:
                break
        else:
            raise ValueError('No such task!')
        j.state = 'queued'
        self._write()

    @lock
    def get_ids(self):
        self._read()
        return {task.id for task in self.tasks}

    def _read(self) -> None:
        if not self.fname.is_file():
            self.number = 0
            return

        data = json.loads(self.fname.read_text())

        self.tasks = [Task.fromdict(dct) for dct in data['tasks']]

        self.number = data['number']

    def _write(self):
        text = json.dumps({'tasks': [task.todict()
                                     for task in self.tasks],
                           'number': self.number},
                          indent=2)
        self.fname.write_text(text)

    @lock
    def update(self, id: int, state: str) -> None:
        if not state.isalpha():
            if state == '0':
                state = 'done'
            else:
                state = 'FAILED'

        n = {'running': 0,
             'done': 1,
             'FAILED': 2,
             'TIMEOUT': 3}[state]

        self.fname.with_name('local-{}-{}'.format(id, n)).write_text('')

        self._read()
        for task in self.tasks:
            if task.id == id:
                break
        else:
            raise ValueError('No such task: {id}, {state}'
                             .format(id=id, state=state))

        if state == 'done':
            tasks = []
            for j in self.tasks:
                if j is not task:
                    if task.dname in j.deps:
                        j.deps.remove(task.dname)
                    tasks.append(j)
            self.tasks = tasks
        elif state == 'running':
            task.state = 'running'
        else:
            assert state in ['FAILED', 'TIMEOUT'], state
            task.state = 'CANCELED'
            task.cancel_dependents(self.tasks, 0)
            self.tasks = [task for task in self.tasks
                          if task.state != 'CANCELED']

        self._kick()
        self._write()

    @lock
    def kick(self) -> None:
        self._read()
        self._kick()
        self._write()

    def _kick(self) -> None:
        for task in self.tasks:
            if task.state == 'running':
                return

        for task in self.tasks:
            if task.state == 'queued' and not task.deps:
                break
        else:
            return

        import os
        sys.stdout.flush()
        pid = os.fork()
        if pid == 0:
            self.locked = False
            # os.chdir('/')
            # os.setsid()
            # os.umask(0)
            # do second fork
            pid = os.fork()
            if pid == 0:
                # redirect standard file descriptors
                sys.stderr.flush()
                si = open(os.devnull, 'r')
                so = open(os.devnull, 'w')
                se = open(os.devnull, 'w')
                os.dup2(si.fileno(), sys.stdin.fileno())
                os.dup2(so.fileno(), sys.stdout.fileno())
                os.dup2(se.fileno(), sys.stderr.fileno())
                self._run(task)
            os._exit(0)
        task.state = 'running'

    def _run(self, task):
        out = '{name}.out'.format(name=task.name)
        err = '{name}.err'.format(name=task.name)

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 -x MPLBACKEND=Agg '
            mpiexec += '-np {} '.format(task.resources.processes)
            cmd = mpiexec + cmd.replace('python3',
                                        config.get('parallel_python',
                                                   'python3'))
        else:
            cmd = 'MPLBACKEND=Agg ' + cmd
        cmd = 'cd {} && {} 2> {} > {}'.format(task.folder, cmd, err, out)
        msg = ('python3 -m myqueue.local {} {}'
               .format(config['home'], task.id))
        cmd = ('({msg} running ; {cmd} ; {msg} $?)& p1=$!; '
               '(sleep {tmax}; kill $p1 > /dev/null 2>&1; {msg} TIMEOUT)& '
               'p2=$!; wait $p1; '
               'if [ $? -eq 0 ]; then kill $p2 > /dev/null 2>&1; fi'
               .format(cmd=cmd, msg=msg, tmax=task.resources.tmax))
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0


if __name__ == '__main__':
    from pathlib import Path
    home, id, state = sys.argv[1:4]
    initialize_config(Path(home))
    q = LocalQueue()
    q.update(int(id), state)
