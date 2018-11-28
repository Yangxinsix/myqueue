============
Installation
============

Get the code and install with ``pip``::

    $ git clone https://gitlab.com/jensj/myqueue.git
    $ cd myqueue
    $ python3 -m pip install --user --editable .

Make sure ``~/.local/bin/`` is in your ``$PATH`` and enable bash tab-completion
like this::

    $ mq completion -q >> ~/.bashrc


Configuration
=============

You need to configure your SLURM/PBS system with a ~/.myqueue/config.py file.
The simplest way is to copy the file from a friend::

    $ ls ~/../*/.myqueue/config.py
    /home/you/../alice/.myqueue/config.py
    /home/you/../bob/.myqueue/config.py
    ...
    $ cp ~alice/.myqueue/config.py ~/.myqueue/config.py


