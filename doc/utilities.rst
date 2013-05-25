Utilities for dealing with exressions
=====================================

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


:mod:`sympy` interface
----------------------

.. automodule:: pymbolic.sympy_interface

.. class:: SympyToPymbolicMapper

    .. method:: __call__(expr)

.. class:: PymbolicToSympyMapper

    .. method:: __call__(expr)
