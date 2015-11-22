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

Why pymbolic when there's already sympy?
========================================

(This is extracted from an email I (Andreas) sent to Aaron Meurer and Anthony
Scopatz.)

So why not use :mod:`sympy` as an AST for DSLs and code generation? It's a good
question. As you read the points I make below, please bear in mind that I'm not
saying this to 'attack' sympy or to diminish the achievement that it is. Very
much on the contrary--as I said above, sympy does a fantastic job being a
computer algebra. I just don't think it's as much in its element as an IR for
code generation. Personally, I think that's perfectly fine--IMO, the tradeoffs
are different for IRs and efficient computer algebra. In a sense, pymbolic
competes much harder with Python's ast module for being a usable program
representation than with Sympy for being a CAS.

At any rate, to answer your question, here goes:

*   First, specifically *because* sympy is smart about its input, and will
    rewrite it behind your back. pymbolic is *intended* to be a dumb and
    static expression tree, and it will leave its input alone unless you
    explicitly tell it not to. In terms of floating point math or around
    custom node types that may or may not obey the same rules as scalars,
    I feel like 'leave it alone' is a safer default.

*   Pickling: https://github.com/sympy/sympy/issues/4297

    The very moment code generation starts taking more than a second or
    so, you'll want to implement a caching mechanism, likely using Pickle.

*   Extensibility of transformation constructs: sympy's built-in traversal
    behaviors (e.g. taking derivatives, conversion to string, code
    generation) aren't particularly easy to extend.  It's important to
    understand what I'm talking about here: I would like to be able to
    make something that, say, is *like* taking a derivative (or
    evaluating, or...), but behaves just a bit differently for a few node
    types. This is a need that I've found to be very common in code
    generation. In (my understanding of) sympy, these behaviors are
    attached to method names, so the only way I could conceivably obtain a
    tweaked "diff" would be to temporarily monkeypatch "diff" for my node
    type, which is kind of a nonstarter. (unless I'm missing something)

    Pymbolic's "mapper" mechanism does somewhat better here--you
    simply inherit from the base behavior, implement/override a few
    methods, and you're done.

    This part is a bit of a red herring though, since this can be
    implemented for sympy (and, in fact, `I have
    <https://github.com/inducer/pymbolic/blob/master/pymbolic/sympy_interface.py#L71>`_).
    Also, I noticed that sympy's codegen module implements something similar (e.g.
    `here
    <https://github.com/sympy/sympy/blob/master/sympy/printing/fcode.py#L174>`_).
    The remaining issue is that most of sympy's behaviors aren't available to
    extend in this style.

*   Representation of code-like constructs, such as:

    *   Indexing

    *   Bit shifts and other bitwise ops:

    *   Distinguishing floor-div and true-div

    *   Attribute Access

*   I should also mention that pymbolic, aside from maintenance and bug
    fixes, is effectively 'finished'. It's pretty tiny, it's not
    ambitious, and it's not going to change much going forward. And that
    is precisely what I want from a package that provides the core data
    structure for something complicated and compiler-ish that I'm building
    on top.

User-visible changes
====================

Version 2015.3
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
