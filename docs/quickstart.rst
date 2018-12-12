=============
A quick start
=============

.. highlight:: bash

::

    $ mkdir proj1
    $ cd proj1
    $ echo "print('Hello world!')" > hello.py
    $ mq submit hello.py
    1 . hello.py 1:10m
    1 task submitted

::

    $ mq ls
    id folder name     res.  age state time error
    -- ------ -------- ---- ---- ----- ---- -----
    1  .      hello.py 1:10m 0:02 done  0:00
    -- ------ -------- ---- ---- ----- ---- -----
    done: 1, total: 1
    $ ls
    hello.py
    hello.py.1.err
    hello.py.1.out
    $ cat hello.py.1.out
    Hello world!

::

    $ cd ..
    $ mkdir proj2
    $ cd proj2
    $ mq submit math:sin -a 3.1415
    2 . math:sin+3.1415 1:10m
    1 task submitted
    $ mq submit math:sin -a hello
    3 . math:sin+hello 1:10m
    1 task submitted

::

    $ mq ls
    id folder name            res.  age state  time error
    -- ------ --------------- ---- ---- ------ ---- ---------------------------------------
    2  .      math:sin+3.1415 1:10m 0:04 done   0:00
    3  .      math:sin+hello  1:10m 0:02 FAILED 0:00 TypeError: must be real number, not str
    -- ------ --------------- ---- ---- ------ ---- ---------------------------------------
    done: 1, FAILED: 1, total: 2
    $ cd ..
    $ mq ls
    id folder  name            res.  age state  time error
    -- ------- --------------- ---- ---- ------ ---- ---------------------------------------
    1  ./proj1 hello.py        1:10m 0:07 done   0:00
    2  ./proj2 math:sin+3.1415 1:10m 0:04 done   0:00
    3  ./proj2 math:sin+hello  1:10m 0:02 FAILED 0:00 TypeError: must be real number, not str
    -- ------- --------------- ---- ---- ------ ---- ---------------------------------------
    done: 2, FAILED: 1, total: 3
    $ mq ls proj1
    id folder  name     res.  age state time error
    -- ------- -------- ---- ---- ----- ---- -----
    1  ./proj1 hello.py 1:10m 0:07 done  0:00
    -- ------- -------- ---- ---- ----- ---- -----
    done: 1, total: 1

::

    $ mq rm -s d proj*
    2 ./proj2 math:sin+3.1415 1:10m 0:05 done 0:00
    1 ./proj1 hello.py        1:10m 0:08 done 0:00
    2 tasks removed

``mq ls ~``.
