import asyncio
import os
import pickle
import socket
import subprocess
import sys
from functools import partial
from pathlib import Path

from .scheduler import Scheduler
from .task import Task


class LocalSchedulerError(Exception):
    pass


class LocalScheduler(Scheduler):
    def send(self, *args):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(('127.0.0.1', 8888))
            b = pickle.dumps(args)
            assert len(b) < 4096
            s.sendall(b)
            b = b''.join(iter(partial(s.recv, 4096), b''))
        status, *args = pickle.loads(b)
        if status != 'ok':
            raise LocalSchedulerError(status)
        return args

    def submit(self, task: Task, activation_script: Path = None,
               dry_run: bool = False) -> None:
        assert not dry_run
        (id,) = self.send('submit', task, activation_script)
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
    def __init__(self):
        self.next_id = 1
        self.processes = {}
        self.tasks = []
        self.queue = asyncio.Queue()

    async def main(self):
        server = await asyncio.start_server(
            self.recv, '127.0.0.1', 8888)

        # self.task = asyncio.create_task(self.execute())

        async with server:
            await server.serve_forever()

    async def execute(self):
        while True:
            task = await self.queue.get()
            print('execute', task)

    async def recv(self, reader, writer):

        data = await reader.read(4096)
        cmd, *args = pickle.loads(data)
        print(cmd, args)
        if cmd == 'submit':
            task, activation_script = args
            self.tasks.append((task, activation_script))
        else:
            1 / 0
        writer.write(pickle.dumps(('ok', 1)))
        await writer.drain()

        print("Close the connection")
        writer.close()
        self.kick()
        print(self.next_id, self.processes, self.tasks)

    async def run(self, task, activation_script):
        id = self.next_id
        self.next_id += 1
        task.id = id
        out = f'{task.cmd.short_name}.{id}.out'
        err = f'{task.cmd.short_name}.{id}.err'

        config = {}
        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 '
            mpiexec += f'-np {task.resources.processes} '
            cmd = mpiexec + cmd.replace('python3',
                                        config.get('parallel_python',
                                                   'python3'))
        cmd = f'{cmd} 2> {err} > {out}'
        proc = await asyncio.create_subprocess_shell(
            cmd, cwd=task.folder)
        self.processes[id] = proc
        loop = asyncio.get_event_loop()
        tmax = task.resources.tmax
        loop.call_later(tmax, self.terminate, proc)
        print('waiting ... 2')
        await proc.wait()
        print('waiting ... 2')

    def terminate(self, proc):
        print(proc)
        if proc.returncode is None:
            proc.terminate()

    async def submittttt(self, task, activation_script):
        loop = asyncio.get_running_loop()
        handle = loop.call_soon(self.run)
        print(dir(handle))

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
        print('kick')
        for task, asc in self.tasks:
            if task.state == 'running':
                return

        for task, asc in self.tasks:
            if task.state == 'queued' and not task.deps:
                break
        else:
            return

        print('run')
        asyncio.create_task(self.run(task, asc))
        task.state = 'running'


if __name__ == '__main__':
    asyncio.run(Server().main())
