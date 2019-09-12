Development
===========

Git repository
--------------

https://gitlab.com/myqueue/myqueue/


Documentation
-------------

Whenever the output of *mq* changes, please update the examples in the
ReST documentation files with::

    $ mq test --update-source-code

Whenever changes are made to the command-line tool, please update the
documentation and tab-completion script with::

    $ python3 -m myqueue.utils


New release
-----------

::

    $ python3 setup.py sdist bdist_wheel
    $ twine upload dist/*
