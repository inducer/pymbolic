Installation
============

This command should install :mod:`pymbolic`::

    pip install pymbolic

You may need to run this with :command:`sudo`.
If you don't already have `pip <https://pypi.python.org/pypi/pip>`_,
run this beforehand::

    curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
    python get-pip.py

For a more manual installation, download the source, unpack it,
and say::

    python setup.py install

User-visible Changes
====================

Version 2013.2
--------------

.. note::

    This version is currently under development. You can get snapshots from
    Pymbolic's `git repository <https://github.com/inducer/pymbolic>`_

* Add :mod:`pymbolic.geometric_algebra`.
* First documented version.

.. _license:

License
=======

:mod:`pymbolic` is licensed to you under the MIT/X Consortium license:

Copyright (c) 2008-13 Andreas Klöckner

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

Frequently Asked Questions
==========================

The FAQ is maintained collaboratively on the
`Wiki FAQ page <http://wiki.tiker.net/Pymbolic/FrequentlyAskedQuestions>`_.

Glossary
========

.. glossary::

    mix-in
        See `Wikipedia article <https://en.wikipedia.org/wiki/Mixin>`_.

        Be sure to mention the mix-in before the base classe being mixed in the
        list of base classes. This way, the mix-in can override base class
        behavior.
