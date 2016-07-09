Alamatic
========

Alamatic is (or, at least, will hopefully grow to become) a programming language
intended to be a good fit for rapid development of embedded applications for
microcontroller platforms like Arduino.

It's currently very early in development, and many language features are
only implemented partially. The language design itself is also in flux.

Dev Environment Setup
---------------------

The compiler is written in Go, targeting Go 1.6. The following instructions
assume you already have a working Go 1.6 development environment.

You can install the compiler as you might expect:

* ``go get github.com/alamatic/alamatic/...``

The compiler depends on [Ragel](http://www.colm.net/open-source/ragel/) for
its scanner component. If you're on a recent version of Ubuntu you can install
this from the main repositories:

* ``sudo apt-get install ragel``

We also use `stringer`:

* ``go get golang.org/x/tools/cmd/stringer``

* ``go install golang.org/x/tools/cmd/stringer``

After you've installed the compiler packets into your `GOPATH` it's necessary
to generate some files within the tokenizer:

* ``go generate github.com/alamatic/alamatic/tokenizer``

The compiler is not yet complete enough to use directly, but you can run
the tests:

* ``go test github.com/alamatic/alamatic/...``
