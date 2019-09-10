====================
Configure your queue
====================

You need to configure your SLURM/PBS system with a ``~/.myqueue/config.py``
file.  The file describes what your system looks like:  Names of the nodes,
number of cores and other things.

.. highlight:: bash

The simplest way is to copy the file from a friend who has already written a
configuration file for you supercomputer::

    $ ls ~/../*/.myqueue/config.py
    /home/you/../alice/.myqueue/config.py
    /home/you/../bob/.myqueue/config.py
    ...
    $ cp ~alice/.myqueue/config.py ~/.myqueue/config.py

.. highlight:: python

Here is an example configuration file:

.. literalinclude:: example_config.py

The type of scheduler you are using must be ``'slurm'``, ``'pbs'`` or
``'local'``.  The *local* scheduler can be used for testing on a system without
SLURM/PBS.

By default, parallel jobs will be started with the ``mpiexec`` command found
on your ``PATH``.  You can specify a different executable with this extra line
in your ``config.py`` file::

    config = {
        ...,
        'mpiexec': '/path/to/your/mpiexec/my-mpiexec',
        ...}

If you want to use an MPI enabled Python interpreter for running your Python
scripts in parallel then you must specify which one you want to use::

    config = {
        ...,
        'parallel_python': 'your-python',
        ...}

Use ``'asap-python'`` for ASAP_ and ``'gpaw-python'`` for GPAW_.  For MPI4PY_,
you don't need an MPI-enabled interpreter.

.. _MPI4PY: https://mpi4py.readthedocs.io/en/stable/index.html
.. _ASAP: https://wiki.fysik.dtu.dk/asap
.. _GPAW: https://wiki.fysik.dtu.dk/gpaw/
