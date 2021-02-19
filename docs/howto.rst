How to ...
==========

Delete lost tasks
-----------------

Tasks were lost, but MyQueue still thinks they are there.  This can
happen if they were deleted with ``scancel``, ``bkill`` or ``qdel`` instead
of ``mq rm``.  Solution:

* Use ``mq sync`` (:ref:`sync`)


Remove many tasks
-----------------

The ``mq rm`` :ref:`command <remove>` can read task ID's from standard input::

    $ cat ids | mq rm -i -
    $ mq ls | grep <something> | mq rm -i -


Start from scratch
------------------

* Remove your ``.myqueue/queue.json`` file.
