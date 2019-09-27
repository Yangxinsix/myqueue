How it works
============

Your queue
----------

When you submit a task, MyQueue will submit it to your scheduler and add it to
a *queue* file (:file:`~/.myqueue/queue.json`).  Once the tasks starts
running (let's say it has a task-id ``1234``), it will write a status file
called ``1234-0`` in your ``~/.myqueue/`` folder.  When the tasks stops
running, it will write a file called ``1234-1`` if it finished successfully
and ``1234-2`` if it failed.  MyQueue will remove the status files and
update your queue with information about timing and possible errors.

The processing of the status files happens whenever you interact with MyQueue
on the command-line or every 10 minutes when the MyQueue daemon wakes up.

All events are logged to ``~/.myqueue/log.csv``.


The daemon
----------

The daemon process wakes up every ten minutes to check if any tasks need to be
resubmitted.  It will write its output to ``~/.myqueue/daemon.out``.

How does the daemon get started?  Whenever the time stamp of the
``daemon.out`` file is older that 2 hours or the file is missing, the *mq*
command will start the daemon process.


More than one configuration file
--------------------------------

If you have several projects and they need diferent scheduler configuration,
then you can use the :ref:`init <init>` command::

    $ mkdir project2
    $ cd project2
    $ mq init
    $ ls .myqueue/
    config.py

You now have a ``project2/.myqueue/`` folder that contains a copy of your main
configuration file (``~/.myqueue/config.py``) that you can edit.  All tasks
inside the ``project2/`` folder will now use ``project2/.myqueue/`` for
storing your queue and configuration.

MyQueue keeps track of all your *root* folders in the file
``~/.myqueue/folders.txt`` so that you can get a quick overview of all your
projects with::

    $ mq ls -AC
    /home/jensj:
    done: 17, total: 17
    /home/jensj/project2:
    done: 42, running 117, total: 159
