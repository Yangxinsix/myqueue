====================
Configure your queue
====================

You need to configure your SLURM/PBS system with a ``~/.myqueue/config.py``
file.  The file describes what your system looks like:  Names of the nodes,
number of cores and other things.

The simplest way is to copy the file from a friend::

    $ ls ~/../*/.myqueue/config.py
    /home/you/../alice/.myqueue/config.py
    /home/you/../bob/.myqueue/config.py
    ...
    $ cp ~alice/.myqueue/config.py ~/.myqueue/config.py


Here is an example configuration file:

.. literalinclude:: example_config.py

The type of queue you are using must be ``'slurm'``, ``'pbs'`` or ``'local'``.

If you are running your Python scripts in parallel then you must specify which
MPI enabled Python interpreter you want to use:

* MPI4PY_: ``'python'``
* ASAP_: ``'asap-python'``
* GPAW_: ``'gpaw-python'``

.. _MPI4PY: https://mpi4py.readthedocs.io/en/stable/index.html
.. _ASAP: https://wiki.fysik.dtu.dk/asap
.. _GPAW: https://wiki.fysik.dtu.dk/gpaw/
