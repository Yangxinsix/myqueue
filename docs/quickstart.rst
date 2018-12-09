=============
A quick start
=============

::

    $ mkdir proj1
    $ cd proj1
    $ echo "print('Hello world!')" > hello.py
    $ mq submit hello.py

::

    $ mq ls
    $ ls
    $ cat hello.py.1.out

::

    $ cd ..
    $ mkdir proj2
    $ cd proj2
    $ mq submit math:sin -a 3.1415
    $ mq submit math:sin -a hello

::

    $ mq ls
    $ cd ..
    $ mq ls
    $ mq ls proj1

::

    $ mq rm -s d proj*

``mq ls ~``.
