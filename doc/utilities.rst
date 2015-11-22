Utilities for dealing with expressions
======================================

Parser
------

.. currentmodule:: pymbolic

.. function:: parse(expr_str)

    Return a :class:`pymbolic.primitives.Expression` tree corresponding to *expr_str*.

The parser is also relatively easy to extend. See the source code of the following
class.

.. automodule:: pymbolic.parser

.. autoclass:: Parser

Compiler
--------

.. automodule:: pymbolic.compiler

.. autoclass:: CompiledExpression

    .. method:: __call__(*args)

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
