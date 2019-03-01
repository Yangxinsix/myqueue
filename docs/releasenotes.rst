=============
Release notes
=============


Next release
============

* New ``--target`` option for :ref:`worflows <worflows>`.
* New ``--name`` option for the :ref:`submit <submit>` command.
* No more ``--arguments`` option.  Use::

    $ mq submit [options] <task> [folder1 [folder2 ...]] -- <arg1> <arg2> ...


Version 19.2.0
==============

* Fix test-suite.


Version 19.1.0
==============

* Recognizes mpiexex variant automatically.

* New "detailed information" subcommand.


Version 18.12.0
===============

* The ``restart`` parameter is now an integer (number of restarts) that
  counts down to zero.  Avoids infinite loop.


Version 0.1.0
=============

Initial release.
