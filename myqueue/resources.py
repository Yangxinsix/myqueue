from typing import List, Dict, Tuple, Any, Union


def seconds_to_short_time_string(n: float) -> str:
    n = int(n)
    for s, t in [('d', 24 * 3600),
                 ('h', 3600),
                 ('m', 60),
                 ('s', 1)]:
        if n % t == 0:
            break

    return '{}{}'.format(n // t, s)


def T(t: str) -> int:
    """Convert string to seconds."""
    return {'s': 1,
            'm': 60,
            'h': 3600,
            'd': 24 * 3600}[t[-1]] * int(t[:-1])


class Resources:
    def __init__(self,
                 cores: int = 1,
                 nodename: str = '',
                 processes: int = 0,
                 tmax: int = 600) -> None:
        self.cores = cores
        self.nodename = nodename
        self.tmax = tmax

        if processes == 0:
            self.processes = cores
        else:
            self.processes = processes

    @staticmethod
    def from_string(s):
        cores, s = s.split(':', 1)
        nodename = ''
        processes = 0
        tmax = 600
        for x in s.split(':'):
            if x[0].isdigit():
                if x[-1].isdigit():
                    processes = int(x)
                else:
                    tmax = T(x)
            else:
                nodename = x
        return Resources(int(cores), nodename, processes, tmax)

    def __str__(self):
        s = str(self.cores)
        if self.nodename:
            s += ':' + self.nodename
        if self.processes != self.cores:
            s += ':' + str(self.processes)
        return s + ':' + seconds_to_short_time_string(self.tmax)

    def todict(self) -> Dict[str, Union[int, str]]:
        dct = {'cores': self.cores}  # type: Dict[str, Union[int, str]]
        if self.processes != self.cores:
            dct['processes'] = self.processes
        if self.tmax != 600:
            dct['tmax'] = self.tmax
        if self.nodename:
            dct['nodename'] = self.nodename
        return dct

    def select(self, nodelist: List[Tuple[str, Dict[str, Any]]]):
        if self.nodename:
            for name, dct in nodelist:
                if name == self.nodename:
                    break
            else:
                raise ValueError('No such node: {}'.format(self.nodename))
        else:
            for name, dct in nodelist:
                if self.cores % dct['cores'] == 0:
                    break
            else:
                _, name, dct = min((dct['cores'], name, dct)
                                   for name, dct in nodelist)

        nodes, rest = divmod(self.cores, dct['cores'])
        if rest:
            nodes += 1

        return nodes, name, dct
