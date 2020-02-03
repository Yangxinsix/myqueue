import asyncio
import os
import pickle
import socket
import subprocess
import sys
from pathlib import Path

from .scheduler import Scheduler
from .task import Task


class LocalSchedulerError(Exception):
    pass


class LocalScheduler(Scheduler):
    def send0(self, *args):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 8888))
            s.sendall(pickle.dumps(args))
            b = s.recv(4096)
        status, *args = pickle.loads(b)
        if status != 'ok':
            raise LocalSchedulerError(status)
        return args

    async def send(self, *args):
        reader, writer = await asyncio.open_connection(
            '127.0.0.1', 8888)

        writer.write(pickle.dumps(args))

        data = await reader.read()
        print(f'Received: {data.decode()!r}')

        print('Close the connection')
        writer.close()
        status, *args = pickle.loads(data)
        if status != 'ok':
            raise LocalSchedulerError(status)
        return args

    def submit(self, task: Task, activation_script: Path = None,
               dry_run: bool = False) -> None:
        assert not dry_run
        # (id,) = self.send('submit', task, activation_script)
        (id,) = asyncio.run(self.send('submit', task, activation_script))
        task.id = id

    def cancel(self, task):
        self.send('cancel', task.id)

    def hold(self, task):
        self.send('hold', task.id)

    def release_hold(self, task):
        self.send('release', task.id)

    def get_ids(self):
        (ids,) = self.send('list')
        return ids


class Server:
    async def main(self):
        server = await asyncio.start_server(
            self.recv, '127.0.0.1', 8888)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

    async def recv(self, reader, writer):
        data = await reader.read()
        cmd, *args = pickle.loads(data)
        print(cmd, args)
        writer.write(pickle.dumps(('ok', 1)))
        await writer.drain()

        print("Close the connection")
        writer.close()

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

        config = {}
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


if __name__ == '__main__':
    asyncio.run(Server().main())
