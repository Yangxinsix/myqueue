import json
import subprocess


from myqueue.config import home_folder
from myqueue.task import Task
from myqueue.queue import Queue


class LocalQueue(Queue, Lock):
    def __init__(self, name):
        Queue.__init__(self, name)
        self.fname = home_folder() / '{}-queue.json'.format(name)
        self.tasks = []
        self.number = None

    def submit(self, task: Task) -> None:
        self._read()
        self.number += 1
        task.id = self.number
        self.tasks.append(task)
        self._write()

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

        for dct in data['tasks']:
            task = Task.fromdict(dct)
            self.tasks.append(task)

        self.number = data['number']

    def _write(self):
        text = json.dumps({'tasks': [task.todict()
                                     for task in self.tasks],
                           'number': self.number})
        self.fname.write_text(text)

    def update(self, id: int, state: str) -> None:
        if not state.isalpha():
            if state == '0':
                state = 'done'
            else:
                state = 'FAILED'

        self.fname.with_name('local-{}-{}'.format(id, state)).write_text('')

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
        else:
            assert state in ['FAILED', 'TIMEOUT'], state
            tasks = []
            for j in self.tasks:
                if j is not task and task.dname not in j.deps:
                    tasks.append(j)
            self.tasks = tasks

            if state == 'TIMEOUT':
                path = task.folder / (task.name + '.err')
                with open(str(path), 'a') as fd:
                    fd.write('\nTIMEOUT\n')

        self._write()
        self.kick()

    def kick(self) -> None:
        self._read()
        for task in self.tasks:
            if task.state == 'running':
                return

        for task in self.tasks:
            if task.state == 'queued' and not task.deps:
                break
        else:
            return

        self._run(task)
        self._write()

    def timeout(self, task):
        path = task.folder / (task.name + '.err')
        if path.is_file():
            task.tstop = path.stat().st_mtime
            lines = path.read_text().splitlines()
            for line in lines[::-1]:
                if line.endswith('TIMEOUT'):
                    return True
        return False

    def _run(self, task):
        cmd1 = task.command()
        msg = 'python3 -m myqueue.local {}'.format(task.id)
        err = task.folder / (task.name + '.err')
        cmd = ('(({msg} running ; {cmd} ; {msg} $?)& p1=$!; '
               '(sleep {tmax}; kill $p1 > /dev/null 2>&1; {msg} TIMEOUT)& '
               'p2=$!; wait $p1; '
               'if [ $? -eq 0 ]; then kill $p2 > /dev/null 2>&1; fi)&'
               .format(cmd=cmd1, msg=msg, tmax=task.tmax, err=err))
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0
        task.state = 'running'


if __name__ == '__main__':
    import sys
    id, state = sys.argv[1:3]
    with LocalQueue() as q:
        q.update(int(id), state)
