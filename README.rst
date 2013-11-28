Pymbolic
========

Pymbolic is a small expression tree and symbolic manipulation library. Two
things set it apart from other libraries of its kind:

* Users can easily write their own symbolic operations, simply by deriving
  from the builtin visitor classes.
* Users can easily add their own symbolic entities to do calculations
  with.

Pymbolic currently understands regular arithmetic expressions, derivatives,
sparse polynomials, fractions, term substitution, expansion. It automatically
performs constant folding, and it can compile its expressions into Python 
bytecode for fast(er) execution.

If you are looking for a full-blown Computer Algebra System, look at 
`sympy <http://pypi.python.org/pypi/sympy>`_ or 
`PyGinac <http://pyginac.sourceforge.net/>`_. If you are looking for a
basic, small and extensible set of symbolic operations, pymbolic may
well be for you.

.. image:: https://badge.fury.io/py/pymbolic.png
    :target: http://pypi.python.org/pypi/pymbolic

Resources:

* `documentation <http://documen.tician.de/pymbolic>`_
* `download <http://pypi.python.org/pypi/pymbolic>`_ (via the package index)
* `source code via git <http://github.com/inducer/pymbolic>`_ (also bug tracker)
