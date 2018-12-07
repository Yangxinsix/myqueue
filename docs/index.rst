=======
MyQueue
=======

MyQueue is a simple frontend for SLURM_ and PBS_.  It has a :ref:`cli` called
``mq`` with a number of :ref:`commands` and a Python_ interface for managing
:ref:`workflows`.

.. warning::

    Do not use this tool unless you know what you are doing!

Features:

* Easy task submission: ``mq submit <task> -R <cores>:<time>``
* Automatic restarting of timed-out/out-of-memory tasks with more time/cores
* :ref:`Workflows`


.. toctree::
    :maxdepth: 3
    :caption: Contents:

    installation
    configuration
    quickstart
    tutorial
    workflows
    cli
    releasenotes


.. _SLURM: https://slurm.schedmd.com/
.. _PBS: http://www.pbspro.org/
.. _Python: https://python.org/


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
