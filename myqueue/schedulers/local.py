from __future__ import annotations

import pickle
import socket
import subprocess
import threading
from functools import partial
from queue import Queue as FIFOQueue
from typing import Any

from myqueue.config import Configuration
from myqueue.queue import Queue
from myqueue.schedulers import Scheduler
from myqueue.states import State
from myqueue.task import Task


class LocalSchedulerError(Exception):
    pass


class LocalScheduler(Scheduler):
    port = 39999

    def submit(self,
               task: Task,
               dry_run: bool = False,
               verbose: bool = False) -> int:
        if dry_run:
            if verbose:
                print(task)
            return 1
        task.cmd.function = None
        id = self.send('submit', task)
        return id

    def cancel(self, id: int) -> None:
        self.send('cancel', id)

    def hold(self, id: int) -> None:
        self.send('hold', id)

    def release_hold(self, id: int) -> None:
        self.send('release', id)

    def get_ids(self) -> set[int]:
        ids = self.send('list')
        return ids

    def send(self, *args: Any) -> Any:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(('127.0.0.1', self.port))
            except ConnectionRefusedError:
                raise ConnectionRefusedError(
                    'Local scheduler not responding.  '
                    'Please start it with:\n\n'
                    '    python3 -m myqueue.schedulers.local')
            b = pickle.dumps(args)
            assert len(b) < 4096
            s.sendall(b)
            if args[0] == 'stop':
                return
            print(len(b))
            b = b''.join(iter(partial(s.recv, 4096), b''))
            #b = s.recv(4096)
            print(len(b))
        status, result = pickle.loads(b)
        print(status, result)
        if status != 'ok':
            raise LocalSchedulerError(status)
        return result

    def get_config(self, queue: str = '') -> tuple[list[tuple[str, int, str]],
                                                   list[str]]:
        return [], []


class Server:
    """Run tasks in subprocesses."""
    def __init__(self,
                 config: Configuration,
                 cores: int = 1,
                 port: int = 39999) -> None:
        self.config = config
        self.port = port

        with Queue(config) as queue:
            maxid = queue.connection.execute(
                'SELECT MAX(id) FROM tasks').fetchone()[0] or 0
            self.next_id = 1 + maxid

        self.tasks: dict[int, Task] = {}
        self.running: dict[int, tuple[threading.Thread, int]] = {}
        self.folder = self.config.home / '.myqueue'
        self.queue = FIFOQueue()
        self.loop_thread = threading.Thread(target=self.loop)

    def run(self) -> None:
        """Start server and wait for commands."""
        self.loop_thread.start()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            print('BIND ...')
            s.bind(('', self.port))
            s.listen(1)
            while True:
                conn, addr = s.accept()
                with conn:
                    print('Connected by', addr)
                    data = conn.recv(1024)
                    cmd, *args = pickle.loads(data)
                    print('COMMAND:', cmd, *args)
                    result = getattr(self, cmd)(*args)
                    print('RESULT:', result)
                    conn.sendall(pickle.dumps(('ok', result)))
                    self.queue.put(cmd)
                    if cmd == 'stop':
                        break
                    print('++++')
        self.loop_thread.join()

    def submit(self, task):
        task.id = self.next_id
        task.state = State.queued
        print([d.id for d in task.dtasks])
        assert all(t.id in self.tasks for t in task.dtasks)
        task.deps = [t.dname for t in task.dtasks]
        self.tasks[task.id] = task
        self.next_id += 1
        return task.id

    def list(self):
        return list(self.tasks)

    def cancel(self, id):
        if id in self.processes:
            self.terminate(id)
        elif id in self.tasks:
            task = self.tasks[id]
            task.state = State.CANCELED
            self.cancel_dependents(task)
        return None

    def loop(self) -> None:
        """Check if a new task should be started."""
        cmd = ''
        while cmd != 'stop':
            cmd = self.queue.get()
            print('LOOP:', cmd)
            self.kick()

    def kick(self):
        remove = []
        for id, (proc, thread) in self.running.items():
            if id not in self.tasks:
                thread.join()
                remove.append(id)
        for id in remove:
            del self.running[id]

        for task in self.tasks.values():
            if task.state == State.running:
                return

        for task in self.tasks.values():
            if task.state == State.queued and not task.deps:
                break
        else:  # no break
            return

        print('START', task.id)
        self.start(task)

    def start(self, task: Task) -> None:
        """Run a task."""
        out = f'{task.cmd.short_name}.{task.id}.out'
        err = f'{task.cmd.short_name}.{task.id}.err'

        cmd = str(task.cmd)
        if task.resources.processes > 1:
            mpiexec = f'{self.config.mpiexec} -x OMP_NUM_THREADS=1 '
            mpiexec += f'-np {task.resources.processes} '
            cmd = mpiexec + cmd.replace('python3',
                                        self.config.parallel_python)
        cmd = f'{cmd} 2> {err} > {out}'

        proc = subprocess.Popen(cmd, shell=True, cwd=task.folder)
        thread = threading.Thread(target=self.target, args=(task.id,))
        self.running[task.id] = (proc, thread)
        thread.start()

    def target(self, id):
        task = self.tasks[id]
        tmax = task.resources.tmax
        task.state = State.running
        (self.folder / f'local-{id}-0').write_text('')  # running
        proc, thread = self.running[id]
        proc.communicate(timeout=tmax)
        print('END', task.id, proc.returncode)
        del self.tasks[task.id]

        if proc.returncode == 0:
            for t in self.tasks.values():
                if task.dname in t.deps:
                    t.deps.remove(task.dname)
            state = 1
        else:
            if task.state == 'TIMEOUT':
                state = 3
            else:
                state = 2
            self.cancel_dependents(task)

        (self.folder / f'local-{task.id}-{state}').write_text('')

        self.queue.put('join')

    def _cancel_dependents(self, task: Task) -> None:
        for job in self.tasks.values():
            print('CANCEL', len(self.tasks), task.dname, job, job.deps)
            if task.dname in job.deps:
                job.state = State.CANCELED
                self._cancel_dependents(job)

    def cancel_dependents(self, task: Task) -> None:
        self._cancel_dependents(task)
        self.tasks = {id: task for id, task in self.tasks.items()
                      if task.state != State.CANCELED}

    def terminate(self, id: int, state: State = State.TIMEOUT) -> None:
        """Terminate a task."""
        print('Terminate', id)
        proc = self.processes.get(id)
        if proc and proc.returncode is None:
            proc.terminate()
            self.tasks[id].state = state


if __name__ == '__main__':
    Server(Configuration.read()).run()
