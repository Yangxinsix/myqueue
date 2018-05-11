from typing import List, Dict, Tuple, Any


class Resources:
    def __init__(self,
                 cores: int,
                 nodename: str,
                 processes: int,
                 tmax: int):
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

    def todict(self) -> Dict[str, Any]:
        dct = {'cores': self.cores}
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
                1 / 0
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


def T(t: str) -> int:
    """Convert string to seconds."""
    return {'s': 1,
            'm': 60,
            'h': 3600,
            'd': 24 * 3600}[t[-1]] * int(t[:-1])
