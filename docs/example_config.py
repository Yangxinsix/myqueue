config = {
    'queue': 'slurm',
    'parallel_python': 'gpaw-python',
    'nodes': [
        ('xeon8', {'cores': 8,
                   'memory': '23G'}),
        ('xeon16', {'cores': 16,
                    'memory': '63G'}),
        ('xeon24', {'cores': 24,
                    'memory': '255G'})]}
