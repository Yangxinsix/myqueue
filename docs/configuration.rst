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

scheduler
=========

The type of scheduler you are using must be ``'slurm'``, ``'pbs'`` or
``'local'``.  The *local* scheduler can be used for testing on a system without
SLURM/PBS.


nodes
=====

This is a list of (name, dictionary) tuples describing the different types
of nodes.  Each dictionary must have a ``cores`` entry.  Other possible keys
that you normally don't need are: ``memory``, ``features``, ``reservation``
and ``mpiargs`` (see the `source code`_ for how to use them).

The order of your nodes is significant.  If you ask for :math:`N` cores,
MyQueue will pick the first type of node from the list that has a core count
that divides :math:`N`.  Given the configuration shown above, here are some
example :ref:`resource <resources>` specifications:

    ``48:12h``: 2 :math:`\times` ``xeon24``

    ``48:xeon8:12h``: 6 :math:`\times` ``xeon8``

    ``48:xeon16:12h``: 3 :math:`\times` ``xeon16``

.. _source code: https://gitlab.com/myqueue/myqueue/blob/master/myqueue/slurm.py


mpiexec
=======

By default, parallel jobs will be started with the ``mpiexec`` command found
on your ``PATH``.  You can specify a different executable with this extra line
in your ``config.py`` file::

    config = {
        ...,
        'mpiexec': '/path/to/your/mpiexec/my-mpiexec',
        ...}


parallel_python
===============

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
