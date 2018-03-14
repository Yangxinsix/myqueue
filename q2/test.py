from q2.job import Job
j1 = Job('a.b:f')
Job('a.b:g', deps=[j1])
