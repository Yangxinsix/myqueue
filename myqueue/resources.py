class Resources:
    def __init__(self,
                 cores: int = None,
                 nodes: int = None,
                 node: str = None,
                 tmax:

    cores, tmax = resources.split('x', 1)
    if ':' in cores:
        cores, processes = cores.split(':')
    else:
        processes = cores

    return int(cores), int(processes), tmax

    def create():
        if res.node:
            if
        for size in [24, 16, 8]:
            if job.cores % size == 0:
                nodes = job.cores // size
                break
        else:
            size = 8
            nodes = job.cores // 8 + 1
                     