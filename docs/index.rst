=======
MyQueue
=======

MyQueue is a frontend for SLURM_/LSF_/PBS_ that makes handling of tasks easy.
It has a command-line interface called ``mq`` with a number of :ref:`commands`
and a Python interface for managing :ref:`workflows`.  Simple to set up: no
system administrator or database required.

.. admonition:: Features

    * Easy task submission:

      * from the command line: ``mq submit <task> -R <cores>:<time>``
      * from Python: :func:`myqueue.submit`

    * Automatic restarting of timed-out/out-of-memory tasks
      with more time/cores

    * Remembers your finished and failed tasks

    * Powerful :ref:`list <list>` command for monitoring

    * Can be used together with Python :mod:`venv`\ 's

    * Folder-based :ref:`Workflows`

Latest release: :ref:`19.11.1 <releases>`.

.. image:: https://gitlab.com/myqueue/myqueue/badges/master/coverage.svg

.. toctree::
    :maxdepth: 3
    :caption: Contents:

    installation
    configuration
    quickstart
    documentation
    howitworks
    cli
    workflows
    api
    releasenotes
    development


.. _SLURM: https://slurm.schedmd.com/
.. _PBS: https://en.m.wikipedia.org/wiki/Portable_Batch_System
.. _LSF: https://en.m.wikipedia.org/wiki/Platform_LSF
.. _Python: https://python.org/


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
