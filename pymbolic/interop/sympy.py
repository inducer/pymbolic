from __future__ import division, absolute_import

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

import pymbolic.primitives as prim
from pymbolic.mapper.evaluator import EvaluationMapper
import sympy as sp

__doc__ = """
.. class:: SympyToPymbolicMapper

    .. method:: __call__(expr)

.. class:: PymbolicToSympyMapper

    .. method:: __call__(expr)
"""


class SympyMapper(object):
    def __call__(self, expr, *args, **kwargs):
        return self.rec(expr, *args, **kwargs)

    def rec(self, expr, *args, **kwargs):
        mro = list(type(expr).__mro__)
        dispatch_class = kwargs.pop("dispatch_class", type(self))

        while mro:
            method_name = "map_"+mro.pop(0).__name__

            try:
                method = getattr(dispatch_class, method_name)
            except AttributeError:
                pass
            else:
                return method(self, expr, *args, **kwargs)

        return self.not_supported(expr)

    def not_supported(self, expr):
        raise NotImplementedError(
                "%s does not know how to map type '%s'"
                % (type(self).__name__,
                    type(expr).__name__))


class CSE(sp.Function):
    """A function to translate to a Pymbolic CSE."""

    nargs = 1


def make_cse(arg, prefix=None):
    result = CSE(arg)
    result.prefix = prefix
    return result


# {{{ sympy -> pymbolic

class SympyToPymbolicMapper(SympyMapper):
    def map_Symbol(self, expr):
        return prim.Variable(expr.name)

    def map_ImaginaryUnit(self, expr):
        return 1j

    def map_Float(self, expr):
        return float(expr)

    def map_Pi(self, expr):
        return float(expr)

    def map_Add(self, expr):
        return prim.Sum(tuple(self.rec(arg) for arg in expr.args))

    def map_Mul(self, expr):
        return prim.Product(tuple(self.rec(arg) for arg in expr.args))

    def map_Rational(self, expr):
        num = self.rec(expr.p)
        denom = self.rec(expr.q)

        if prim.is_zero(denom-1):
            return num
        return prim.Quotient(num, denom)

    def map_Pow(self, expr):
        return prim.Power(self.rec(expr.base), self.rec(expr.exp))

    def map_Subs(self, expr):
        return prim.Substitution(self.rec(expr.expr),
                tuple(v.name for v in expr.variables),
                tuple(self.rec(v) for v in expr.point),
                )

    def map_Derivative(self, expr):
        return prim.Derivative(self.rec(expr.expr),
                tuple(v.name for v in expr.variables))

    def map_CSE(self, expr):
        return prim.CommonSubexpression(
                self.rec(expr.args[0]), expr.prefix)

    def not_supported(self, expr):
        if isinstance(expr, int):
            return expr
        elif getattr(expr, "is_Function", False):
            return prim.Variable(type(expr).__name__)(
                    *tuple(self.rec(arg) for arg in expr.args))
        else:
            return SympyMapper.not_supported(self, expr)

# }}}


# {{{ pymbolic -> sympy

class PymbolicToSympyMapper(EvaluationMapper):
    def map_variable(self, expr):
        return sp.Symbol(expr.name)

    def map_constant(self, expr):
        return sp.sympify(expr)

    def map_call(self, expr):
        if isinstance(expr.function, prim.Variable):
            func_name = expr.function.name
            try:
                func = getattr(sp.functions, func_name)
            except AttributeError:
                func = sp.Function(func_name)
            return func(*[self.rec(par) for par in expr.parameters])
        else:
            raise RuntimeError("do not know how to translate '%s' to sympy"
                    % expr)

    def map_subscript(self, expr):
        if isinstance(expr.aggregate, prim.Variable) and isinstance(expr.index, int):
            return sp.Symbol("%s_%d" % (expr.aggregate.name, expr.index))
        else:
            raise RuntimeError("do not know how to translate '%s' to sympy"
                    % expr)

    def map_substitution(self, expr):
        return sp.Subs(self.rec(expr.child),
                tuple(sp.Symbol(v) for v in expr.variables),
                tuple(self.rec(v) for v in expr.values),
                )

    def map_derivative(self, expr):
        return sp.Derivative(self.rec(expr.child),
                *[sp.Symbol(v) for v in expr.variables])

# }}}

# vim: fdm=marker
