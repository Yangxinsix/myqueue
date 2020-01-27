Development
===========

Git repository
--------------

Code, merge requests and issues can be found here:

    https://gitlab.com/myqueue/myqueue/

Contributions and suggestions for improvements are very welcome.


Getting help
------------

For discussions, questions and help, go to our `#myqueue` stream on
https://camd.zulipchat.com/.


Testing
-------

Run the tests like this:

    $ pytest [...]

and report any errors you get: https://gitlab.com/myqueue/myqueue/issues.


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
