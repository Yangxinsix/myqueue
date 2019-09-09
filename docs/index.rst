=======
MyQueue
=======

MyQueue is a frontend for SLURM_ and PBS_ that makes handling of tasks easy.
It has a :ref:`cli` called ``mq`` with a number of :ref:`commands` and a
Python_ interface for managing :ref:`workflows`.  Simple to set up: no system
administrator or database required.

Features:

* Easy task submission:

  * from the command line: ``mq submit <task> -R <cores>:<time>``
  * from Python: :func:`myqueue.submit`

* Automatic restarting of timed-out/out-of-memory tasks with more time/cores

* Remembers your finished and failed tasks.

* Powerfull ``mq list`` command for monitoring.

* :ref:`Workflows`


.. toctree::
    :maxdepth: 3
    :caption: Contents:

    installation
    configuration
    quickstart
    tutorial
    api
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
