"""Resource class to handle resource requirements: time, cores, processes."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Tuple, Dict

if TYPE_CHECKING:
    from myqueue.commands import Command

from myqueue.states import State

Node = Tuple[str, Dict[str, Any]]

RESOURCES_URL = (
    'https://myqueue.readthedocs.io/en/latest/documentation.html#resources')


def seconds_to_short_time_string(n: float) -> str:
    """Convert seconds to time string.

    >>> seconds_to_short_time_string(42)
    '42s'
    >>> seconds_to_short_time_string(7200)
    '2h'
    """
    n = int(n)
    for s, t in [('d', 24 * 3600),
                 ('h', 3600),
                 ('m', 60),
                 ('s', 1)]:
        if n % t == 0:
            break

    return f'{n // t}{s}'


def T(t: str) -> int:
    """Convert string to seconds."""
    return {'s': 1,
            'm': 60,
            'h': 3600,
            'd': 24 * 3600}[t[-1]] * int(t[:-1])


class Resources:
    """Resource description."""
    def __init__(self,
                 cores: int = 0,
                 nodename: str = '',
                 processes: int = 0,
                 tmax: int = 0,
                 weight: float = -1.0):
        """Resource object.

        cores: int
            Number of cores.
        nodename: str
            Name of node.
        processes: int
            Number of processes to start.
        tmax: str
            Maximum time for task.  Examples: "40s", "30m", "20h" and "2d".
        weight: float
            Weight of task.  See :ref:`task_weight`.
        """
        self.cores = cores or 1
        self.nodename = nodename
        self.tmax = tmax or 600  # seconds
        self.weight = weight

        if processes == 0:
            self.processes = self.cores
        else:
            self.processes = processes

    def set_default_weight(self, weight: float) -> None:
        if self.weight == -1.0:
            self.weight = weight

    @staticmethod
    def from_string(s: str) -> Resources:
        """Create Resource object from string.

        >>> Resources.from_string('16:1:xeon8:2h')
        Resources(cores=16, processes=1, tmax=7200, nodename='xeon8')
        >>> Resources.from_string('16:1m')
        Resources(cores=16, tmax=60)
        >>> r = Resources.from_string('16:1m:25')
        >>> r
        Resources(cores=16, tmax=60, weight=25.0)
        >>> print(r)
        16:1m:25
        """
        nodename = ''
        processes = 0
        weight = -1.0
        try:
            p1, *parts = s.split(':')
            cores = int(p1)
            if parts[-1][-1] not in 'smhd':
                weight = float(parts.pop())
            tmax = T(parts.pop())
            for p in parts:
                if p.isdigit():
                    processes = int(p)
                else:
                    nodename = p
        except ValueError as ex:
            raise ValueError(
                f'Bad resource string: {s!r}.  See {RESOURCES_URL}') from ex

        return Resources(cores, nodename, processes, tmax, weight)

    @staticmethod
    def from_args_and_command(cores: int = 0,
                              nodename: str = '',
                              processes: int = 0,
                              tmax: str = '',
                              weight: float = -1.0,
                              resources: str = '',
                              command: Command = None,
                              path: Path = None) -> Resources:
        all_defaults = (cores == 0 and
                        nodename == ''
                        and processes == 0
                        and tmax == '' and
                        weight == -1.0)
        if all_defaults:
            if resources:
                return Resources.from_string(resources)
            assert command is not None and path is not None
            res = command.read_resources(path)
            if res is not None:
                return res
        else:
            if resources != '':
                url = 'https://myqueue.readthedocs.io/en/latest'
                raise ValueError(
                    f'resources={resources!r} can\'t be combined with '
                    '"cores", "nodename", "processes", "tmax" or "weight". '
                    f'See {url}/documentation.html#resources')

        return Resources(cores, nodename, processes, T(tmax or '10m'), weight)

    def __str__(self) -> str:
        s = str(self.cores)
        if self.nodename:
            s += ':' + self.nodename
        if self.processes != self.cores:
            s += ':' + str(self.processes)
        s += ':' + seconds_to_short_time_string(self.tmax)
        if self.weight > 0.0:
            s += f':{int(self.weight)}'
        return s

    def __repr__(self) -> str:
        args = ', '.join(f'{key}={value!r}'
                         for key, value in self.todict().items())
        return f'Resources({args})'

    def todict(self) -> dict[str, Any]:
        """Convert to dict."""
        dct: dict[str, float | int | str] = {'cores': self.cores}
        if self.processes != self.cores:
            dct['processes'] = self.processes
        if self.tmax != 600:
            dct['tmax'] = self.tmax
        if self.nodename:
            dct['nodename'] = self.nodename
        if self.weight != -1.0:
            dct['weight'] = self.weight
        return dct

    def bigger(self,
               state: State,
               nodelist: list[Node],
               maxtmax: int = 2 * 24 * 3600) -> Resources:
        """Create new Resource object with larger tmax or more cores.

        >>> nodes = [('node1', {'cores': 8})]
        >>> r = Resources(tmax=100, cores=8)
        >>> r.bigger(State.TIMEOUT, nodes)
        Resources(cores=8, tmax=200)
        >>> r.bigger(State.MEMORY, nodes)
        Resources(cores=16, tmax=100)
        """
        new = Resources(**self.todict())
        if state == 'TIMEOUT':
            new.tmax = int(min(self.tmax * 2, maxtmax))
        elif state == 'MEMORY':
            coreslist = sorted({dct['cores'] for name, dct in nodelist})
            nnodes = 1
            while True:
                for c in coreslist:
                    cores = nnodes * c
                    if cores > self.cores:
                        break
                else:
                    nnodes += 1
                    continue
                break
            if self.processes == self.cores:
                new.processes = cores
            new.cores = cores
        else:
            raise ValueError
        return new

    def select(self, nodelist: list[Node]) -> tuple[int, str, dict[str, Any]]:
        """Select appropriate node.

        >>> nodes = [('node1', {'cores': 16}),
        ...          ('node2', {'cores': 8}),
        ...          ('fatnode2', {'cores': 8})]
        >>> Resources(cores=24).select(nodes)
        (3, 'node2', {'cores': 8})
        >>> Resources(cores=32).select(nodes)
        (2, 'node1', {'cores': 16})
        >>> Resources(cores=32, nodename='fatnode2').select(nodes)
        (4, 'fatnode2', {'cores': 8})
        >>> Resources(cores=1).select(nodes)
        (1, 'node2', {'cores': 8})
        >>> Resources(cores=32, nodename='node3').select(nodes)
        Traceback (most recent call last):
            ...
        ValueError: No such node: node3
        """
        if self.nodename:
            for name, dct in nodelist:
                if name == self.nodename:
                    break
            else:  # no break
                raise ValueError(f'No such node: {self.nodename}')
        else:
            for name, dct in nodelist:
                if dct.get('special'):
                    continue
                if self.cores % dct['cores'] == 0:
                    break
            else:  # no break
                node = min(nodelist, key=lambda node: node[1]['cores'])
                name, dct = node

        nodes, rest = divmod(self.cores, dct['cores'])
        if rest:
            nodes += 1

        return nodes, name, dct
