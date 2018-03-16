from q2.job import Job
j1 = Job('q2.test.f')
Job('q2.test.g', deps=[j1])
