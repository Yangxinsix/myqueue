=============
A quick start
=============

.. This file contains computer generated output.  Do not touch.

.. highlight:: bash

.. mq: cd /tmp; rm -r .myqueue proj1 proj2

Let's create a simple "Hello world" Python script::

    $ mkdir proj1
    $ cd proj1
    $ echo 'print("Hello world")' > hello.py

and :ref:`submit <submit>` it::

    $ mq submit hello.py
    1 ./ hello.py 1:10m
    1 task submitted

The :ref:`list <list>` command shows that the job is done::

    $ mq ls
    id folder name     res.   age state time
    ── ────── ──────── ───── ──── ───── ────
    1  ./     hello.py 1:10m 0:00 done  0:00
    ── ────── ──────── ───── ──── ───── ────
    done: 1, total: 1

The ``1:10m`` means that 1 core and 10 minutes was reserved for the task.
There is now an output file and an empty error file in the folder::

    $ ls -l
    total 8
    -rw-rw-r-- 1 jensj jensj 21 Apr  6 11:25 hello.py
    -rw-rw-r-- 1 jensj jensj  0 Apr  6 11:25 hello.py.1.err
    -rw-rw-r-- 1 jensj jensj 12 Apr  6 11:25 hello.py.1.out
    $ cat hello.py.1.out
    Hello world

Now we run some calculations in another folder::

    $ cd ..
    $ mkdir proj2
    $ cd proj2
    $ mq submit -R 1:10s "math@sin 3.14"
    2 ./ math@sin 3.14 +1 1:10s
    1 task submitted

This will call the :func:`~math.sin` function from the Python :mod:`math`
module with an argument of ``3.14`` and we ask for 10 seconds on 1 core.
Let's also submit a task that will fail::

    $ mq submit "math@sin hello"
    3 ./ math@sin hello +1 1:10m
    1 task submitted

The :ref:`list <list>` command shows the status of the two tasks in the
current folder::

    $ mq ls
    id folder name     args  info res.   age state  time error
    ── ────── ──────── ───── ──── ───── ──── ────── ──── ───────────────────────────────────────
    2  ./     math@sin 3.14  +1   1:10s 0:00 done   0:00
    3  ./     math@sin hello +1   1:10m 0:00 FAILED 0:00 TypeError: must be real number, not str
    ── ────── ──────── ───── ──── ───── ──── ────── ──── ───────────────────────────────────────
    done: 1, FAILED: 1, total: 2

To see the status of both the ``proj1`` and ``proj2`` folders, do this::

    $ cd ..
    $ mq ls
    id folder   name     args  info res.   age state  time error
    ── ──────── ──────── ───── ──── ───── ──── ────── ──── ───────────────────────────────────────
    1  ./proj1/ hello.py            1:10m 0:00 done   0:00
    2  ./proj2/ math@sin 3.14  +1   1:10s 0:00 done   0:00
    3  ./proj2/ math@sin hello +1   1:10m 0:00 FAILED 0:00 TypeError: must be real number, not str
    ── ──────── ──────── ───── ──── ───── ──── ────── ──── ───────────────────────────────────────
    done: 2, FAILED: 1, total: 3

See status of the ``proj1`` folder only::

    $ mq ls proj1
    id folder   name     res.   age state time
    ── ──────── ──────── ───── ──── ───── ────
    1  ./proj1/ hello.py 1:10m 0:00 done  0:00
    ── ──────── ──────── ───── ──── ───── ────
    done: 1, total: 1

Once you have seen that your tasks have finished, you will typically remove
them so that only queued and failed tasks are left::

    $ mq rm -s d proj*
    1 ./proj1/ hello.py         1:10m 0:00 done 0:00
    2 ./proj2/ math@sin 3.14 +1 1:10s 0:00 done 0:00
    2 tasks removed

.. tip::

    Use ``mq ls ~`` to see all your tasks.
