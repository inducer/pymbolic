Welcome to pymbolic!
====================

Pymbolic is a simple and extensible package for precise manipulation of
symbolic expressions in Python. It doesn't try to compete with :mod:`sympy` as
a computer algebra system. Pymbolic emphasizes providing an extensible
expression tree and a flexible, extensible way to manipulate it.

A taste of :mod:`pymbolic`
--------------------------

Follow along on a simple example. Let's import :mod:`pymbolic` and create a
symbol, *x* in this case.

.. doctest::

    >>> import pymbolic as pmbl

    >>> x = pmbl.var("x")
    >>> x
    Variable('x')

Next, let's create an expression using *x*:

.. doctest::

    >>> u = (x+1)**5
    >>> u
    Power(Sum((Variable('x'), 1)), 5)
    >>> print(u)
    (x + 1)**5

Note the two ways an expression can be printed, namely :func:`repr` and
:class:`str`.  :mod:`pymbolic` purposefully distinguishes the two.

:mod:`pymbolic` does not perform any manipulations on expressions
you put in. It has a few of those built in, but that's not really the point:

.. doctest::

    >>> print(pmbl.differentiate(u, 'x'))
    5*(x + 1)**4

.. _custom-manipulation:

Manipulating expressions
^^^^^^^^^^^^^^^^^^^^^^^^

The point is for you to be able to easily write so-called *mappers* to
manipulate expressions. Suppose we would like all sums replaced by
products:

.. doctest::

    >>> from pymbolic.mapper import IdentityMapper
    >>> class MyMapper(IdentityMapper):
    ...     def map_sum(self, expr):
    ...         return pmbl.primitives.Product(expr.children)
    ...
    >>> print(u)
    (x + 1)**5
    >>> print(MyMapper()(u))
    (x*1)**5

Custom Objects
^^^^^^^^^^^^^^

You can also easily define your own objects to use inside an expression:

.. doctest::

    >>> from pymbolic import ExpressionNode, expr_dataclass
    >>> from pymbolic.typing import Expression
    >>>
    >>> @expr_dataclass()
    ... class FancyOperator(ExpressionNode):
    ...     operand: Expression
    ...
    >>> u
    Power(Sum((Variable('x'), 1)), 5)
    >>> 17*FancyOperator(u)
    Product((17, FancyOperator(Power(Sum((..., 1)), 5))))

As a final example, we can now derive from *MyMapper* to multiply all
*FancyOperator* instances by 2.

.. doctest::

    >>> FancyOperator.mapper_method
    'map_fancy_operator'
    >>> class MyMapper2(MyMapper):
    ...     def map_fancy_operator(self, expr):
    ...         return 2*FancyOperator(self.rec(expr.operand))
    ...
    >>> MyMapper2()(FancyOperator(u))
    Product((2, FancyOperator(Power(Product((..., 1)), 5))))

.. automodule:: pymbolic

Pymbolic around the web
-----------------------

* `PyPI package <https://pypi.org/project/pymbolic/>`__
* `Documentation <https://documen.tician.de/pymbolic/>`__
* `Source code (GitHub) <https://github.com/inducer/pymbolic>`__

Contents
--------

.. toctree::
   :maxdepth: 2

   primitives
   mappers
   utilities
   algorithms
   geometric-algebra
   misc
   🚀 Github <https://github.com/inducer/pymbolic>
   💾 Download Releases <https://pypi.org/project/pymbolic>

* :ref:`genindex`
* :ref:`modindex`

.. vim: sw=4
