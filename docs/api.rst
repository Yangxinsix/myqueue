Python API
==========

.. module:: myqueue

.. autofunction:: myqueue.submit

.. module:: myqueue.task

Don't create the :class:`myqueue.task.Task` object directly --- use the
:func:`myqueue.task.task` function instead.

.. autofunction:: myqueue.task.task

.. autoclass:: myqueue.task.Task
   :members: submit
