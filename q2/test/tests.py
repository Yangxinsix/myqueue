import os
from q2.queue import Queue
from q2.job import Job, jobstates


def run_tests():
    os.environ['Q2_HOME'] = 'testing'
    q = Queue('local')
    q.submit([Job('time')])
    q.list(None, None, jobstates, [])
    q.list(None, None, jobstates, [])
    