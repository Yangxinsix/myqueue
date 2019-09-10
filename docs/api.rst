Python API
==========

.. module:: myqueue

Simple examples
---------------

::

    from myqueue.task import task
    task('./script.py', tmax='2d', cores=24).submit()

The helper function :func:`myqueue.task.task` makes it easy to create
:class:`myqueue.task.Task` objects.  The :func:`myqueue.submit` function
can be used if you want to submit several tasks at the same time::

    from myqueue import submit
    from myqueue.task import task
    tasks = [task('mymodule@func', args=[arg], tmax='2d', cores=24)
             for arg in [42, 117, 999]]
    submit(*tasks)


Advanced example
----------------

::

    from myqueue.commands import PythonModule
    from myqueue.resources import Resources
    from myqueue.task import Task

    task = Task(PythonModule('module', []),
                Resources(cores=8, tmax=3600)
    task.submit()


API
---

.. autofunction:: myqueue.submit
.. module:: myqueue.task
.. autofunction:: myqueue.task.task
.. autoclass:: myqueue.task.Task
   :members: submit
.. autofunction:: myqueue.commands.command
.. autoclass:: myqueue.commands.ShellCommand
.. autoclass:: myqueue.commands.ShellScript
.. autoclass:: myqueue.commands.PythonScript
.. autoclass:: myqueue.commands.PythonModule
.. autoclass:: myqueue.commands.PythonFunction
.. autoclass:: myqueue.resources.Resources
.. autoclass:: myqueue.queue.Queue
.. autoclass:: myqueue.slurm.SLURM
.. autoclass:: myqueue.pbs.PBS
