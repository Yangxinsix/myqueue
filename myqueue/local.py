import asyncio
import pickle
import socket
from functools import partial
from pathlib import Path
from typing import Any, Set, Tuple, List

from .config import config, initialize_config
from .scheduler import Scheduler
from .task import Task


class LocalSchedulerError(Exception):
    pass


class LocalScheduler(Scheduler):
    def submit(self, task: Task, dry_run: bool = False) -> None:
        assert not dry_run
        (id,) = self.send('submit', task)
        task.id = id

    def cancel(self, task: Task) -> None:
        self.send('cancel', task.id)

    def hold(self, task) -> None:
        self.send('hold', task.id)

    def release_hold(self, task) -> None:
        self.send('release', task.id)

    def get_ids(self) -> Set[int]:
        (ids,) = self.send('list')
        return ids

    def send(self, *args) -> Tuple[Any, ...]:
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

    def get_config(self) -> List[Tuple[str, int, str]]:
        return []


class Server:
    def __init__(self):
        self.next_id = 1
        self.processes = {}
        self.tasks = []
        self.folder = config['home'] / '.myqueue'

    async def main(self):
        server = await asyncio.start_server(
            self.recv, '127.0.0.1', 8888)

        # self.task = asyncio.create_task(self.execute())

        async with server:  # type: ignore
            await server.serve_forever()

    async def recv(self, reader, writer):

        data = await reader.read(4096)
        cmd, *args = pickle.loads(data)
        print(cmd, args)
        if cmd == 'submit':
            task = args[0]
            task.id = self.next_id
            self.next_id += 1
            self.tasks.append(task)
            result = (task.id,)
        else:
            1 / 0
        writer.write(pickle.dumps(('ok',) + result))
        await writer.drain()
        writer.close()
        self.kick()
        print(self.next_id, self.processes, self.tasks)

    def kick(self) -> None:
        for task in self.tasks:
            if task.state == 'running':
                return

        for task in self.tasks:
            if task.state == 'queued' and not task.deps:
                break
        else:
            return

        asyncio.create_task(self.run(task))

    async def run(self, task):
        out = f'{task.cmd.short_name}.{task.id}.out'
        err = f'{task.cmd.short_name}.{task.id}.err'

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
        loop.call_later(tmax, self.terminate, proc, task)
        task.state = 'running'
        (self.folder / f'local-{task.id}-0').write_text('')  # running
        await proc.wait()
        self.tasks.remove(task)
        if proc.returncode == 0:
            for t in self.tasks:
                if task.dname in t.deps:
                    t.deps.remove(task.dname)
            state = 1
        else:
            if task.state == 'TIMEOUT':
                state = 3
            else:
                state = 2
            task.cancel_dependents(self.tasks)
            self.tasks = [task for task in self.tasks
                          if task.state != 'CANCELED']
        (self.folder / f'local-{task.id}-{state}').write_text('')
        self.kick()

    def terminate(self, proc, task):
        if proc.returncode is None:
            proc.terminate()
            task.state = 'TIMEOUT'


if __name__ == '__main__':
    initialize_config(Path.cwd())
    asyncio.run(Server().main())
