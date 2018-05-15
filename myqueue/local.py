import json
import subprocess


from myqueue.config import home_folder
from myqueue.queue import Queue
from myqueue.task import Task
from myqueue.utils import Lock, lock


class LocalQueue(Queue, Lock):
    def __init__(self):
        self.fname = home_folder() / 'local.json'
        Lock.__init__(self, self.fname.with_name('local.json.lock'))
        self.tasks = []
        self.number = None

    @lock
    def submit(self, task: Task) -> None:
        self._read()
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

    def _read(self) -> None:
        if not self.fname.is_file():
            self.number = 0
            return

        data = json.loads(self.fname.read_text())

        self.tasks = [Task.fromdict(dct) for dct in data['tasks']]

        self.number = data['number']

    def _write(self):
        print('WRITE')
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

        print('LOCAL', n, state)
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
                    print('RM', task.dname, j.deps)
                    print('RM', type(task.dname), [type(d) for d in j.deps])
                    if task.dname in j.deps:
                        j.deps.remove(task.dname)
                    tasks.append(j)
            self.tasks = tasks
        elif state == 'running':
            task.state = 'running'
        else:
            assert state in ['FAILED', 'TIMEOUT'], state
            tasks = []
            for j in self.tasks:
                if j is not task and task.dname not in j.deps:
                    tasks.append(j)
            self.tasks = tasks

        self._kick()
        self._write()

    @lock
    def kick(self) -> None:
        self._read()
        self._kick()
        self._write()

    def _kick(self) -> None:
        print('KICK', [(t.state, t.deps) for t in self.tasks])
        for task in self.tasks:
            if task.state == 'running':
                return

        for task in self.tasks:
            if task.state == 'queued' and not task.deps:
                break
        else:
            return

        self._run(task)

    def _run(self, task):
        cmd1 = task.command()
        msg = 'python3 -m myqueue.local {}'.format(task.id)
        err = task.folder / (task.name + '.err')
        cmd = ('(({msg} running ; {cmd} ; {msg} $?)& p1=$!; '
               '(sleep {tmax}; kill $p1 > /dev/null 2>&1; {msg} TIMEOUT)& '
               'p2=$!; wait $p1; '
               'if [ $? -eq 0 ]; then kill $p2 > /dev/null 2>&1; fi)&'
               .format(cmd=cmd1, msg=msg, tmax=task.resources.tmax, err=err))
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0
        task.state = 'running'


if __name__ == '__main__':
    import sys
    id, state = sys.argv[1:3]
    q = LocalQueue()
    q.update(int(id), state)
