from q2.job import Job


def workflow():
    j1 = Job('sleep+5')
    j2 = Job('echo+j2', deps=[j1])
    jobs = [
        j1,
        j2,
        Job('echo+j3', deps=[j1]),
        Job('echo+j4', deps=[j2])]
    return jobs
