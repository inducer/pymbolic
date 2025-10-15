Utilities for dealing with expressions
======================================

Parser
------

.. currentmodule:: pymbolic

.. autofunction:: parse

The parser is also relatively easy to extend. See the source code of the following
class.

.. automodule:: pymbolic.parser

Compiler
--------

.. automodule:: pymbolic.compiler

Interoperability with other symbolic systems
============================================

Interoperability with :mod:`sympy`
----------------------------------

.. automodule:: pymbolic.interop.sympy

Interoperability with Maxima
----------------------------

.. automodule:: pymbolic.interop.maxima

Interoperability with Python's :mod:`ast` module
------------------------------------------------

.. automodule:: pymbolic.interop.ast

Interoperability with :mod:`matchpy.functions` module
-----------------------------------------------------

.. automodule:: pymbolic.interop.matchpy

Visualizing Expressions
=======================

.. autofunction:: pymbolic.imperative.utils.get_dot_dependency_graph
