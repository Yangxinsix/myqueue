from q2.job import Job
j1 = Job('q2.test.create+j1_0@1x1s')
Job('q2.test.create+j1b_100', deps=[j1])
Job('q2.test.timeout+j1@1x1m', deps=[j1])
j3 = Job('time.sleep+3.5@1x1m', deps=[j1])
Job('q2.test.memory@1x2m', deps=[j3])
Job('q2.test.memory@3x2m', deps=[j3])
