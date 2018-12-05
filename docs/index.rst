=======
MyQueue
=======

MyQueue is a simple frontend for SLURM_ and PBS_.  It has a :ref:`cli` called
``mq`` with a number of subcomands and a Python_ interface for managing
:ref:`workflows`.

.. warning::

    Do not use this unless you know what you are doing!

Features:

* Easy task submission ``mq submit <task> -R <cores>:<time>``
* Restarting of timed-out tasks with more time
* Restarting of out-of-memory tasks on more cores
* One queue for each project (directory tree)
* Workflows


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
