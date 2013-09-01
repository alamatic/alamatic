Alamatic
========

Alamatic is (or, at least, will hopefully grow to become) a programming language
intended to be a good fit for rapid development of embedded applications for
microcontroller platforms like Arduino.

It's currently very early in development, and many language features are
only implemented partially. The language design itself is also in flux.

Dev Environment Setup
---------------------

The compiler and related tools are written in Python, targeting Python 2.7.
The following instructions assume you already have a working Python 2.7
development environment with virtualenv available.

The following steps will turn a fresh git clone into a working dev environment:

* ``virtualenv env``

* ``source env/bin/activate``

* ``pip install -e .``

* ``pip install --pre plex==2.0.0dev`` (to force installation of a pre-release)

* ``pip install -U -r requirements-dev.txt``

After running the above steps you should be able to run the tests using
``nosetests``.
