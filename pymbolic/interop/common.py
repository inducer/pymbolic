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


class SympyLikeMapperBase(object):

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
        print(expr, expr.__class__.__mro__)
        raise NotImplementedError(
                "%s does not know how to map type '%s'"
                % (type(self).__name__,
                    type(expr).__name__))


# {{{ sympy like -> pymbolic

class SympyLikeToPymbolicMapper(SympyLikeMapperBase):

    # {{{ utils

    def to_float(self, expr):
        return float(expr)

    def function_name(self, expr):
        # Given a symbolic function application f(x), return the name of f as a
        # string
        raise NotImplementedError()

    # }}}

    def map_Symbol(self, expr):  # noqa
        return prim.Variable(str(expr.name))

    def map_Rational(self, expr):  # noqa
        p, q = expr.p, expr.q

        num = self.rec(p)
        denom = self.rec(q)

        if prim.is_zero(denom-1):
            return num
        return prim.Quotient(num, denom)

    def map_Integer(self, expr):  # noqa
        return int(expr)

    def map_Add(self, expr):  # noqa
        return prim.Sum(tuple(self.rec(arg) for arg in expr.args))

    def map_Mul(self, expr):  # noqa
        return prim.Product(tuple(self.rec(arg) for arg in expr.args))

    def map_Pow(self, expr):  # noqa
        base, exp = expr.args
        return prim.Power(self.rec(base), self.rec(exp))

    def map_Subs(self, expr):  # noqa
        return prim.Substitution(self.rec(expr.expr),
                tuple(v.name for v in expr.variables),
                tuple(self.rec(v) for v in expr.point),
                )

    def map_Derivative(self, expr):  # noqa
        return prim.Derivative(self.rec(expr.expr),
                tuple(v.name for v in expr.variables))

    def map_CSE(self, expr):  # noqa
        return prim.CommonSubexpression(
                self.rec(expr.args[0]), expr.prefix)

    def not_supported(self, expr):
        if isinstance(expr, int):
            return expr
        elif getattr(expr, "is_Function", False):
            return prim.Variable(self.function_name(expr))(
                    *tuple(self.rec(arg) for arg in expr.args))
        else:
            return SympyLikeMapperBase.not_supported(self, expr)

# }}}


# {{{ pymbolic -> sympy like

class PymbolicToSympyLikeMapper(EvaluationMapper):

    def map_variable(self, expr):
        return self.sym.Symbol(expr.name)

    def map_constant(self, expr):
        return self.sym.sympify(expr)

    def map_call(self, expr):
        if isinstance(expr.function, prim.Variable):
            func_name = expr.function.name
            try:
                func = getattr(self.sym.functions, func_name)
            except AttributeError:
                func = self.sym.Function(func_name)
            return func(*[self.rec(par) for par in expr.parameters])
        else:
            self.raise_conversion_error(expr)

    def map_subscript(self, expr):
        if isinstance(expr.aggregate, prim.Variable) and isinstance(expr.index, int):
            return self.sym.Symbol("%s_%d" % (expr.aggregate.name, expr.index))
        else:
            self.raise_conversion_error(expr)

    def map_substitution(self, expr):
        return self.sym.Subs(self.rec(expr.child),
                tuple(self.sym.Symbol(v) for v in expr.variables),
                tuple(self.rec(v) for v in expr.values),
                )

    def map_derivative(self, expr):
        raise NotImplementedError()

# }}}

# vim: fdm=marker
