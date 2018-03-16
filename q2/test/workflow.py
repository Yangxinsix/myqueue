from q2.job import Job
j1 = Job('q2.test.create_j1_0@1x1s')
Job('q2.test.create_j1b_100', deps=[j1])
j3 = Job('q2.test.timeout_j1@1x1mx10', deps=[j1])
Job('q2.test.memory@1,2,3x2m', deps=[j3])
