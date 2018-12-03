====================
Configure your queue
====================

You need to configure your SLURM/PBS system with a ``~/.myqueue/config.py``
file.  The simplest way is to copy the file from a friend::

    $ ls ~/../*/.myqueue/config.py
    /home/you/../alice/.myqueue/config.py
    /home/you/../bob/.myqueue/config.py
    ...
    $ cp ~alice/.myqueue/config.py ~/.myqueue/config.py


Here is an example configuration file:

.. literalinclude:: example_config.py
