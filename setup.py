#!/usr/bin/env python
# -*- coding: latin-1 -*-

import distribute_setup
distribute_setup.use_setuptools()

from setuptools import setup

setup(name="pymbolic",
      version="2013.1",
      description="A package for symbolic computation",
      long_description="""
      Pymbolic is a small symbolic manipulation library. Two things set it apart
      from other libraries of its kind:

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
      """,
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Other Audience',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        ],
      author=u"Andreas Kloeckner",
      author_email="inform@tiker.net",
      license = "MIT",
      url="http://mathema.tician.de/software/pymbolic",

      packages=["pymbolic", "pymbolic.mapper"],
      install_requires=[
          'pytools>=2'
          ],

     )
