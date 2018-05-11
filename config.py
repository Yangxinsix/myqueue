config = {
    'slurm': {
        'nodes': [
            ('xeon8', {'cores': 8, 'memory': '23G'}),
            ('xeon16', {'cores': 16, 'memory': '63G'}),
            ('xeon24', {'cores': 24,
                        'memory': '255G',
                        'mpiargs': '-mca pml cm -mca mtl psm2'}),
            ('xeon24_512', {'cores': 24,
                            'memory': '511G',
                            'mpiargs': '-mca pml cm -mca mtl psm2'})
        ],
        'parallel-python': 'gpaw-python'
    }
}
