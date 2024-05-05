====================
Configure your queue
====================

You need to configure your SLURM/PBS/LSF system with a ``~/.myqueue/config.py``
file.  The file describes what your system looks like:  Names of the nodes,
number of cores and other things.

.. highlight:: bash

The simplest way is to copy the file from a friend who has already written a
configuration file for you supercomputer::

    $ ls ~/../*/.myqueue/config.py
    /home/you/../alice/.myqueue/config.py
    /home/you/../bob/.myqueue/config.py
    ...
    $ mkdir ~/.myqueue
    $ cp ~alice/.myqueue/config.py ~/.myqueue/

.. highlight:: python

Here is an example configuration file:

.. literalinclude:: example_config.py

The configuration file uses Python syntax to define a dictionary called
``config``.  The dictionary can have the following key-value pairs
(``scheduler`` is requred, the rest are optional):

.. list-table::

   * - Key
     - Description
     - type
     - default
   * - ``scheduler``
     - :ref:`scheduler`
     - ``str``
     -
   * - ``nodes``
     - :ref:`nodes`
     - ``list[tuple[str, dict[str, Any]]]``
     - ``[]``
   * - ``mpiexec``
     - :ref:`mpiexec`
     - ``str``
     - ``'mpiexec'``
   * - ``parallel_python``
     - :ref:`parallel_python`
     - ``str``
     - ``'python3'``
   * - ``serial_python``
     - :ref:`serial_python`
     - ``str``
     - ``'python3'``
   * - ``extra_args``
     - :ref:`extra_args`
     - ``list[str]``
     - ``[]``
   * - ``maximum_total_task_weight``
     - :ref:`task_weight`
     - ``float``
     - ``inf``
   * - ``default_task_weight``
     - :ref:`task_weight`
     - ``float``
     - ``0.0``
   * - ``notifications``
     - :ref:`notifications`
     - ``dict[str, str]``
     - ``{}``

See details below.


.. _autoconfig:

Guessing your configuration
===========================

.. highlight:: bash

Try the following :ref:`command <config>`::

    $ mq config
    ...

It will try to guess your configuration.  It can be a good starting point
for a ``config.py`` file.  You may need to help ``mq config`` a bit by
giving it the scheduler name and/or the queue name (try ``mq config -h``).


.. _scheduler:

Name of scheduler
=================

The type of scheduler you are using must be ``'slurm'``, ``'pbs'``, ``'lsf'``
or ``'local'``.  The *local* scheduler can be used for testing on a system
without SLURM/LSF/PBS.  Start the local scheduler with::

    $ python3 -m myqueue.local


.. highlight:: python


.. _nodes:

Description of node types
=========================

This is a list of ``('<node-name>', <dictionary>)`` tuples describing the
different types of nodes::

    ('xeon24', {'cores': 24, 'memory': '255GB'})

.. highlight:: bash

The node-name is what SLURM calls a partition-name and you would use it like
this::

    $ sbatch --partition=<node-name> ... script

or like this with a PBS system::

    $ qsub -l nodes=<node-name>:ppn=... ... script

Each dictionary must have the following entries:

* ``cores``: Number of cores for the node type.

* ``memory``: The memory available for the entire node.  Specified as a string
  such as ``'500GiB'``.  MyQueue understands the following memory units:
  ``MB``, ``MiB``, ``GB`` and ``GiB``.

Other possible keys that you normally don't need are:, ``extra_args``,
``mpiargs`` (see the `source code`_ for how to use them).

The order of your nodes is significant.  If you ask for :math:`N` cores,
MyQueue will pick the first type of node from the list that has a core count
that divides :math:`N`.  Given the configuration shown above, here are some
example :ref:`resource <resources>` specifications:

    ``48:12h``: 2 :math:`\times` *xeon24*

    ``48:xeon8:12h``: 6 :math:`\times` *xeon8*

    ``48:xeon16:12h``: 3 :math:`\times` *xeon16*


.. _source code: https://gitlab.com/myqueue/myqueue/blob/master/myqueue/slurm.py

.. _mpiexec:

MPI-run command
===============

.. highlight:: python

By default, parallel jobs will be started with the ``mpiexec`` command found
on your ``PATH``.  You can specify a different executable with this extra line
in your ``config.py`` file::

    config = {
        ...,
        'mpiexec': '/path/to/your/mpiexec/my-mpiexec',
        ...}


.. _parallel_python:

Parallel Python interpreter
===========================

If you want to use an MPI enabled Python interpreter for running your Python
scripts in parallel then you must specify which one you want to use::

    config = {
        ...,
        'parallel_python': 'your-python',
        ...}

Use ``'asap-python'`` for ASAP_ and ``'gpaw python'`` for GPAW_.
For MPI4PY_, you don't need an MPI-enabled interpreter.

.. _MPI4PY: https://mpi4py.readthedocs.io/en/stable/index.html
.. _ASAP: https://wiki.fysik.dtu.dk/asap
.. _GPAW: https://wiki.fysik.dtu.dk/gpaw


.. _serial_python:

Serial Python interpreter
=========================

By defaul, ``python3`` is used as the Python interpreter for serial jobs.
Use the ``serial_python`` configuration variable if you want to set it to
something else.


.. _extra_args:

Extra arguments for submit command
==================================

Add extra arguments to the ``sbatch``, ``qsub`` or ``bsub`` command.
Example::

    config = {
        ...,
        'extra_args': ['arg1', 'arg2'],
        'nodes': [
            ('xeon24', {'cores': 24, 'extra_args': ['arg3', 'arg4']}),
            ...],
        ...}

would give ``<submit command> arg1 arg2 arg3 arg4``.


.. _task_weight:

Task weight
===========

In order to limit the number of tasks running at the same time, you can
submit them like this:

.. highlight:: bash

::

    $ mq submit ... -R 24:2h:5  # sets weight to 5

(see :ref:`resources`) or mark them in your workflow script like this:

.. highlight:: python

::

    run(..., weight=5)

and set a global maximum::

    config = {
        ...,
        'maximum_total_task_weight': 100,
        ...}

This will allow only 100 / 5 = 20 tasks in the ``running`` or ``queued``
state. If you submit more that 20 tasks then some of them will be put in the
``hold`` state.  As tasks finish successfully (``done`` state), tasks will be
moved from ``hold`` to ``queued``.

One use case would be to limit the disk-space used by running tasks. Note that
tasks that fail will be counted as still running, so you will have to ``mq
rm`` those and also remember to remove big files left behind.

One can also change the default task weight of 0 to something else by
setting the ``default_task_weight`` configuration variable.


.. _notifications:

Notifications
=============

::

    config = {
        ...,
        'notifications': {'email': 'you@somewhere.org',
                          'host': 'smtp.somewhere.org'
                          'username': 'name'},
        ...}
