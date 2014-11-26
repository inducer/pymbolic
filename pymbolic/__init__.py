from __future__ import division
from __future__ import absolute_import

__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


__doc__ = """
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
    >>> print u
    (x + 1)**5

Note the two ways an expression can be printed, namely :func:`repr` and
:func:`str`.  :mod:`pymbolic` purposefully distinguishes the two.

:mod:`pymbolic` does not perform any manipulations on expressions
you put in. It has a few of those built in, but that's not really the point:

.. doctest::

    >>> print pmbl.differentiate(u, 'x')
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
    >>> print u
    (x + 1)**5
    >>> print MyMapper()(u)
    (x*1)**5

Custom Objects
^^^^^^^^^^^^^^

You can also easily define your own objects to use inside an expression:

.. doctest::

    >>> from pymbolic.primitives import Expression
    >>> class FancyOperator(Expression):
    ...     def __init__(self, operand):
    ...         self.operand = operand
    ...
    ...     def __getinitargs__(self):
    ...         return (self.operand,)
    ...
    ...     mapper_method = "map_fancy_operator"
    ...
    >>> u
    Power(Sum((Variable('x'), 1)), 5)
    >>> 17*FancyOperator(u)
    Product((17, FancyOperator(Power(Sum((Variable('x'), 1)), 5))))

As a final example, we can now derive from *MyMapper* to multiply all
*FancyOperator* instances by 2.

.. doctest::

    >>> class MyMapper2(MyMapper):
    ...     def map_fancy_operator(self, expr):
    ...         return 2*FancyOperator(self.rec(expr.operand))
    ...
    >>> MyMapper2()(FancyOperator(u))
    Product((2, FancyOperator(Power(Product((Variable('x'), 1)), 5))))
"""

from pymbolic.version import VERSION_TEXT as __version__  # noqa

import pymbolic.parser
import pymbolic.compiler

import pymbolic.mapper.evaluator
import pymbolic.mapper.stringifier
import pymbolic.mapper.dependency
import pymbolic.mapper.substitutor
import pymbolic.mapper.differentiator
import pymbolic.mapper.distributor
import pymbolic.mapper.flattener
import pymbolic.primitives

from pymbolic.polynomial import Polynomial  # noqa

var = pymbolic.primitives.Variable
variables = pymbolic.primitives.variables
flattened_sum = pymbolic.primitives.flattened_sum
subscript = pymbolic.primitives.subscript
flattened_product = pymbolic.primitives.flattened_product
quotient = pymbolic.primitives.quotient
linear_combination = pymbolic.primitives.linear_combination
cse = pymbolic.primitives.make_common_subexpression
make_sym_vector = pymbolic.primitives.make_sym_vector

disable_subscript_by_getitem = pymbolic.primitives.disable_subscript_by_getitem

parse = pymbolic.parser.parse
evaluate = pymbolic.mapper.evaluator.evaluate
evaluate_kw = pymbolic.mapper.evaluator.evaluate_kw
compile = pymbolic.compiler.compile
substitute = pymbolic.mapper.substitutor.substitute
diff = differentiate = pymbolic.mapper.differentiator.differentiate
expand = pymbolic.mapper.distributor.distribute
distribute = pymbolic.mapper.distributor.distribute
flatten = pymbolic.mapper.flattener.flatten
