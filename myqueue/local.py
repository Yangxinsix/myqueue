import asyncio
import pickle
import socket
from functools import partial
from typing import Any, Set, Tuple, List

from .scheduler import Scheduler
from .task import Task
from .config import Configuration
from .states import State


class LocalSchedulerError(Exception):
    pass


class LocalScheduler(Scheduler):
    def submit(self,
               task: Task,
               dry_run: bool = False,
               verbose: bool = False) -> None:
        if dry_run:
            id = 1
        else:
            task.cmd.function = None
            id = self.send('submit', task)
        task.id = id

    def cancel(self, task: Task) -> None:
        self.send('cancel', task.id)

    def hold(self, task: Task) -> None:
        self.send('hold', task.id)

    def release_hold(self, task: Task) -> None:
        self.send('release', task.id)

    def get_ids(self) -> Set[int]:
        ids = self.send('list')
        return ids

    def send(self, *args: Any) -> Any:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(('127.0.0.1', 8888))
            except ConnectionRefusedError:
                raise ConnectionRefusedError(
                    'Local scheduler not responding.  '
                    'Please start it with: "python -m myqueue.local"')
            b = pickle.dumps(args)
            assert len(b) < 4096
            s.sendall(b)
            b = b''.join(iter(partial(s.recv, 4096), b''))
        status, result = pickle.loads(b)
        if status != 'ok':
            raise LocalSchedulerError(status)
        return result

    def get_config(self, queue: str = '') -> Tuple[List[Tuple[str, int, str]],
                                                   List[str]]:
        return [], []


class Server:
    def __init__(self,
                 config: Configuration,
                 cores: int = 1,
                 port: int = 39999) -> None:
        self.config = config
        self.port = port
        self.next_id = 1
        self.tasks: List[Task] = []
        self.folder = self.config.home / '.myqueue'

    async def main(self) -> None:
        self.server = await asyncio.start_server(
            self.recv, '127.0.0.1', 8888)

        async with self.server:  # type: ignore
            await self.server.serve_forever()
            await self.server.wait_closed()

    def start(self):
        try:
            asyncio.run(self.main())
        except asyncio.exceptions.CancelledError:
            pass

    async def recv(self, reader: Any, writer: Any) -> None:

        data = await reader.read(4096)
        cmd, *args = pickle.loads(data)
        print(cmd, args)
        if cmd == 'stop':
            self.server.close()
            result = None
        elif cmd == 'submit':
            task = args[0]
            task.id = self.next_id
            self.next_id += 1
            self.tasks.append(task)
            result = task.id
        elif cmd == 'list':
            result = [task.id for task in self.tasks]
        else:
            1 / 0
        writer.write(pickle.dumps(('ok', result)))
        await writer.drain()
        writer.close()
        self.kick()
        print(self.next_id, self.tasks)

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

    async def run(self, task: Task) -> None:
        out = f'{task.cmd.short_name}.{task.id}.out'
        err = f'{task.cmd.short_name}.{task.id}.err'

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = 'mpiexec -x OMP_NUM_THREADS=1 '
            mpiexec += f'-np {task.resources.processes} '
            cmd = mpiexec + cmd.replace('python3',
                                        self.config.parallel_python)
        cmd = f'{cmd} 2> {err} > {out}'
        proc = await asyncio.create_subprocess_shell(
            cmd, cwd=task.folder)
        loop = asyncio.get_event_loop()
        tmax = task.resources.tmax
        loop.call_later(tmax, self.terminate, proc, task)
        task.state = State.running
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

    def terminate(self, proc: Any, task: Task) -> None:
        if proc.returncode is None:
            proc.terminate()
            task.state = State.TIMEOUT


if __name__ == '__main__':
    asyncio.run(Server(Configuration.read()).main())
