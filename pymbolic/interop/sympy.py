from __future__ import division, absolute_import

__copyright__ = """
Copyright (C) 2017 Matt Wala
Copyright (C) 2009-2013 Andreas Kloeckner
"""

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

from pymbolic.interop.common import (
    SympyLikeToPymbolicMapper, PymbolicToSympyLikeMapper)

import pymbolic.primitives as prim
from functools import partial

import sympy


__doc__ = """
.. class:: SympyToPymbolicMapper

    .. method:: __call__(expr)

.. class:: PymbolicToSympyMapper

    .. method:: __call__(expr)
"""


# {{{ sympy -> pymbolic

class SympyToPymbolicMapper(SympyLikeToPymbolicMapper):

    def map_ImaginaryUnit(self, expr):  # noqa
        return 1j

    map_Float = SympyLikeToPymbolicMapper.to_float

    map_NumberSymbol = SympyLikeToPymbolicMapper.to_float

    def function_name(self, expr):
        return type(expr).__name__

    # only called for Py2
    def map_long(self, expr):
        return long(expr)  # noqa

    def map_Indexed(self, expr):  # noqa
        return prim.Subscript(
            self.rec(expr.args[0].args[0]),
            tuple(self.rec(i) for i in expr.args[1:])
            )

    def map_Piecewise(self, expr):  # noqa
        # We only handle piecewises with 2 arguments!
        assert len(expr.args) == 2
        # We only handle if/else cases
        assert expr.args[1][1].is_Boolean and bool(expr.args[1][1]) is True
        then = self.rec(expr.args[0][0])
        else_ = self.rec(expr.args[1][0])
        cond = self.rec(expr.args[0][1])
        return prim.If(cond, then, else_)

    def _comparison_operator(self, expr, operator=None):
        left = self.rec(expr.args[0])
        right = self.rec(expr.args[1])
        return prim.Comparison(left, operator, right)

    map_Equality = partial(_comparison_operator, operator="==")
    map_Unequality = partial(_comparison_operator, operator="!=")
    map_GreaterThan = partial(_comparison_operator, operator=">=")
    map_LessThan = partial(_comparison_operator, operator="<=")
    map_StrictGreaterThan = partial(_comparison_operator, operator=">")
    map_StrictLessThan = partial(_comparison_operator, operator="<")

# }}}


# {{{ pymbolic -> sympy

class PymbolicToSympyMapper(PymbolicToSympyLikeMapper):

    sym = sympy

    def raise_conversion_error(self, expr):
        raise RuntimeError(
            "do not know how to translate '%s' to sympy" % expr)

    def map_derivative(self, expr):
        return self.sym.Derivative(self.rec(expr.child),
                *[self.sym.Symbol(v) for v in expr.variables])

    def map_subscript(self, expr):
        return self.sym.tensor.indexed.Indexed(
            self.rec(expr.aggregate),
            *tuple(self.rec(i) for i in expr.index_tuple)
            )

    def map_if(self, expr):
        cond = self.rec(expr.condition)
        return self.sym.Piecewise((self.rec(expr.then), cond),
                                  (self.rec(expr.else_), True)
                                  )

    def map_comparison(self, expr):
        left = self.rec(expr.left)
        right = self.rec(expr.right)
        if expr.operator == "==":
            return self.sym.Equality(left, right)
        elif expr.operator == "!=":
            return self.sym.Unequality(left, right)
        elif expr.operator == "<":
            return self.sym.StrictLessThan(left, right)
        elif expr.operator == ">":
            return self.sym.StrictGreaterThan(left, right)
        elif expr.operator == "<=":
            return self.sym.LessThan(left, right)
        elif expr.operator == ">=":
            return self.sym.GreaterThan(left, right)
        else:
            raise NotImplementedError("Unknown operator '%s'" % expr.operator)

# }}}


class CSE(sympy.Function):
    """A function to translate to a Pymbolic CSE."""
    nargs = 1


def make_cse(arg, prefix=None):
    result = CSE(arg)
    result.prefix = prefix
    return result


# vim: fdm=marker
