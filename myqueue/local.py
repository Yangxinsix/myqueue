import json
import os
import pickle
import socket
import subprocess
import sys
from pathlib import Path

from .config import config, initialize_config
from .scheduler import Scheduler
from .task import Task


LocalSchedulerError(Exception):
    pass


class LocalScheduler(Scheduler):
    def send(self, *args):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 8888))
            s.sendall(pickle.dumps(args))
            chunks = []
            while True:
                b = s.recv(4096)
                if b:
                    chunks.append(b)
                else:
                    break
        status, *args = pickle.loads(b''.join(chunks))
        if status != 'ok':
            raise LocalSchedulerError(status)
        return args

    def submit(self, task: Task, activation_script: Path = None,
               dry_run: bool = False) -> None:
        assert not dry_run
        id, = self.send('submit', task, activation_script)
        task.id = id

    @lock
    def cancel(self, task):
        assert task.state == 'queued', task
        self._read()
        for i, j in enumerate(self.tasks):
            if task.id == j.id:
                break
        else:
            return
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

        self.tasks = [Task.fromdict(dct, self.root) for dct in data['tasks']]

        self.number = data['number']

    def _write(self):
        text = json.dumps({'tasks': [task.todict(self.root)
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

        self.fname.with_name(f'local-{id}-{n}').write_text('')

        self._read()
        for task in self.tasks:
            if task.id == id:
                break
        else:
            raise ValueError(f'No such task: {id}, {state}')

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
        out = f'{task.cmd.short_name}.{task.id}.out'
        err = f'{task.cmd.short_name}.{task.id}.err'

        testing = os.environ.get('MYQUEUE_TESTING')

        cmd = str(task.cmd)
        if task.resources.processes > 1 and not testing:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 -x MPLBACKEND=Agg '
            mpiexec += f'-np {task.resources.processes} '
            cmd = mpiexec + cmd.replace('python3',
                                        config.get('parallel_python',
                                                   'python3'))
        else:
            cmd = 'MPLBACKEND=Agg ' + cmd
        cmd = f'cd {task.folder} && {cmd} 2> {err} > {out}'
        msg = f"python3 -m myqueue.local {config['home']} {task.id}"
        tmax = task.resources.tmax
        cmd = (f'({msg} running ; {cmd} ; {msg} $?)& p1=$!; '
               f'(sleep {tmax}; kill $p1 > /dev/null 2>&1; {msg} TIMEOUT)& '
               'p2=$!; wait $p1; '
               'if [ $? -eq 0 ]; then kill $p2 > /dev/null 2>&1; fi')
        p = subprocess.run(cmd, shell=True)
        assert p.returncode == 0


class

if __name__ == '__main__':
    import asyncio

    async def handle_echo(reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')

        print(f"Received {message!r} from {addr!r}")

        print(f"Send: {message!r}")
        writer.write(data)
        await writer.drain()

        print("Close the connection")
        writer.close()

    async def main():
        server = await asyncio.start_server(
            handle_echo, '127.0.0.1', 8888)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

    asyncio.run(main())
