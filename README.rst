Pymbolic: Easy Expression Trees and Term Rewriting
==================================================

.. image:: https://gitlab.tiker.net/inducer/pymbolic/badges/main/pipeline.svg
    :alt: Gitlab Build Status
    :target: https://gitlab.tiker.net/inducer/pymbolic/commits/main
.. image:: https://github.com/inducer/pymbolic/workflows/CI/badge.svg?branch=main&event=push
    :alt: Github Build Status
    :target: https://github.com/inducer/pymbolic/actions?query=branch%3Amain+workflow%3ACI+event%3Apush
.. image:: https://badge.fury.io/py/pymbolic.png
    :alt: Python Package Index Release Page
    :target: https://pypi.org/project/pymbolic/
.. image:: https://zenodo.org/badge/2016193.svg
    :alt: Zenodo DOI for latest release
    :target: https://zenodo.org/badge/latestdoi/2016193

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

Resources:

* `documentation <http://documen.tician.de/pymbolic>`_
* `download <http://pypi.python.org/pypi/pymbolic>`_ (via the package index)
* `source code via git <http://github.com/inducer/pymbolic>`_ (also bug tracker)
