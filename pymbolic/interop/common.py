from __future__ import annotations


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

from functools import partial

import pymbolic.primitives as prim
from pymbolic.mapper.evaluator import EvaluationMapper


class SympyLikeMapperBase:

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
                "{} does not know how to map type '{}'".format(
                    type(self).__name__,
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
        return prim.Sum(tuple([self.rec(arg) for arg in expr.args]))

    def map_Mul(self, expr):  # noqa
        return prim.Product(tuple([self.rec(arg) for arg in expr.args]))

    def map_Pow(self, expr):  # noqa
        base, exp = expr.args
        return prim.Power(self.rec(base), self.rec(exp))

    def map_Subs(self, expr):  # noqa
        return prim.Substitution(self.rec(expr.expr),
                tuple([v.name for v in expr.variables]),
                tuple([self.rec(v) for v in expr.point]),
                )

    def map_Derivative(self, expr):  # noqa
        return prim.Derivative(self.rec(expr.expr),
                tuple([v.name for v in expr.variables]))

    def map_UnevaluatedExpr(self, expr):  # noqa
        return self.rec(expr.args[0])

    def not_supported(self, expr):
        if isinstance(expr, int):
            return expr
        elif getattr(expr, "is_Function", False):
            if self.function_name(expr) == "Indexed":
                args = [self.rec(arg) for arg in expr.args]
                if len(args) == 2:
                    return prim.Subscript(args[0], args[1])
                else:
                    return prim.Subscript(args[0], tuple(args[1:]))
            return prim.Variable(self.function_name(expr))(
                    *[self.rec(arg) for arg in expr.args])
        else:
            return SympyLikeMapperBase.not_supported(self, expr)

    def _comparison_operator(self, expr, operator=None):
        left = self.rec(expr.args[0])
        right = self.rec(expr.args[1])
        return prim.Comparison(left, operator, right)

    map_Equality = partial(_comparison_operator, operator="==")  # noqa: N815
    map_Unequality = partial(_comparison_operator, operator="!=")  # noqa: N815  # spellchecker: disable-line
    map_GreaterThan = partial(_comparison_operator, operator=">=")  # noqa: N815
    map_LessThan = partial(_comparison_operator, operator="<=")  # noqa: N815
    map_StrictGreaterThan = partial(_comparison_operator, operator=">")  # noqa: N815
    map_StrictLessThan = partial(_comparison_operator, operator="<")  # noqa: N815

# }}}


# {{{ pymbolic -> sympy like

class PymbolicToSympyLikeMapper(EvaluationMapper):

    @property
    def sym(self):
        raise NotImplementedError

    def raise_conversion_error(self, message):
        raise NotImplementedError

    def map_variable(self, expr):
        return self.sym.Symbol(expr.name)

    def map_constant(self, expr):
        return self.sym.sympify(expr)

    def map_floor_div(self, expr):
        return self.sym.floor(self.rec(expr.numerator) / self.rec(expr.denominator))

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
        if isinstance(expr.aggregate, prim.Variable):
            return self.sym.Function("Indexed")(expr.aggregate.name,
                *(self.rec(idx) for idx in expr.index_tuple))
        else:
            self.raise_conversion_error(expr)

    def map_substitution(self, expr):
        return self.sym.Subs(self.rec(expr.child),
                tuple([self.sym.Symbol(v) for v in expr.variables]),
                tuple([self.rec(v) for v in expr.values]),
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
            return self.sym.Unequality(left, right)  # spellchecker: disable-line
        elif expr.operator == "<":
            return self.sym.StrictLessThan(left, right)
        elif expr.operator == ">":
            return self.sym.StrictGreaterThan(left, right)
        elif expr.operator == "<=":
            return self.sym.LessThan(left, right)
        elif expr.operator == ">=":
            return self.sym.GreaterThan(left, right)
        else:
            raise NotImplementedError(f"Unknown operator '{expr.operator}'")

    def map_derivative(self, expr):
        return self.sym.Derivative(self.rec(expr.child),
                *[self.sym.Symbol(v) for v in expr.variables])

# }}}

# vim: fdm=marker
