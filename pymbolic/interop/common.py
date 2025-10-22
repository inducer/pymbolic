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

from typing import TYPE_CHECKING, Any, Generic, TypeAlias

from typing_extensions import override

import pymbolic.primitives as prim
from pymbolic.mapper import P, ResultT
from pymbolic.mapper.evaluator import EvaluationMapper
from pymbolic.typing import ArithmeticExpression, Expression


if TYPE_CHECKING:
    import optype
    import sympy as sp


class SympyLikeMapperBase(Generic[ResultT, P]):
    def __call__(self, expr: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.rec(expr, *args, **kwargs)

    def rec(self, expr: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        mro = list(type(expr).__mro__)
        dispatch_class = kwargs.pop("dispatch_class", type(self))

        while mro:
            method_name = f"map_{mro[0].__name__}"
            mro.pop(0)

            method = getattr(dispatch_class, method_name, None)
            if method is not None:
                return method(self, expr, *args, **kwargs)

        return self.not_supported(expr)

    def not_supported(self, expr: object) -> ResultT:
        print(expr, expr.__class__.__mro__)
        raise NotImplementedError(
                "{} does not know how to map type '{}'".format(
                    type(self).__name__,
                    type(expr).__name__))


# {{{ sympy like -> pymbolic

class SympyLikeToPymbolicMapper(SympyLikeMapperBase[Expression, []]):

    def rec_arith(self, expr: object) -> ArithmeticExpression:
        result = self.rec(expr)
        assert prim.is_arithmetic_expression(result)

        return result

    # {{{ utils

    def to_float(self, expr: optype.CanFloat) -> Expression:
        return float(expr)

    def function_name(self, expr: object) -> str:
        # Given a symbolic function application f(x), return the name of f as a
        # string
        raise NotImplementedError(f"'function_name' for type {type(expr)}")

    # }}}

    # FIXME(pyright): This class will be used by both sympy and symengine, so this
    # type annotations is not correct.
    def map_Symbol(self, expr: sp.Symbol) -> Expression:
        return prim.Variable(str(expr.name))

    def map_Rational(self, expr: sp.Rational) -> Expression:
        p, q = expr.p, expr.q

        num = self.rec_arith(p)
        denom = self.rec_arith(q)

        if prim.is_zero(denom - 1):
            return num

        return prim.Quotient(num, denom)

    def map_Integer(self, expr: sp.Integer) -> Expression:
        return int(expr)

    def map_Add(self, expr: sp.Add) -> Expression:
        return prim.Sum(tuple([self.rec_arith(arg) for arg in expr.args]))

    def map_Mul(self, expr: sp.Mul) -> Expression:
        return prim.Product(tuple([self.rec_arith(arg) for arg in expr.args]))

    def map_Pow(self, expr: sp.Pow) -> Expression:
        base, exp = expr.args
        return prim.Power(self.rec_arith(base), self.rec_arith(exp))

    def map_Subs(self, expr: sp.Subs) -> Expression:
        return prim.Substitution(
                self.rec(expr.expr),
                tuple([v.name for v in expr.variables]),
                tuple([self.rec_arith(v) for v in expr.point]),
                )

    def map_Derivative(self, expr: sp.Derivative) -> Expression:
        return prim.Derivative(
                self.rec_arith(expr.expr),
                tuple([v.name for v in expr.variables]))

    def map_UnevaluatedExpr(self, expr: sp.UnevaluatedExpr) -> Expression:
        return self.rec(expr.args[0])

    @override
    def not_supported(self, expr: object) -> Expression:
        if isinstance(expr, int):
            return expr
        elif getattr(expr, "is_Function", False):
            # NOTE: see SympyToPymbolicMapper.map_subscript
            if self.function_name(expr) == "Indexed":
                args = [self.rec(arg) for arg in expr.args]
                if len(args) == 2:
                    return prim.Subscript(args[0], args[1])
                else:
                    return prim.Subscript(args[0], tuple(args[1:]))

            return prim.Variable(self.function_name(expr))(
                    *[self.rec(arg) for arg in expr.args])
        else:
            return SympyLikeMapperBase["Expression", []].not_supported(self, expr)

    def _comparison_operator(self, expr: sp.Basic, *, operator: str) -> Expression:
        left = self.rec(expr.args[0])
        right = self.rec(expr.args[1])
        return prim.Comparison(left, operator, right)

    def map_Equality(self, expr: sp.Equality) -> Expression:
        return self._comparison_operator(expr, operator="==")

    def map_Unequality(self, expr: sp.Unequality) -> Expression:  # spellchecker: disable-line  # noqa: E501
        return self._comparison_operator(expr, operator="!=")

    def map_GreaterThan(self, expr: sp.GreaterThan) -> Expression:
        return self._comparison_operator(expr, operator=">=")

    def map_LessThan(self, expr: sp.LessThan) -> Expression:
        return self._comparison_operator(expr, operator="<=")

    def map_StrictGreaterThan(self, expr: sp.StrictGreaterThan) -> Expression:
        return self._comparison_operator(expr, operator=">")

    def map_StrictLessThan(self, expr: sp.StrictLessThan) -> Expression:
        return self._comparison_operator(expr, operator="<")


# }}}


# {{{ pymbolic -> sympy like

SympyLikeExpression: TypeAlias = "sp.Expr"


class PymbolicToSympyLikeMapper(EvaluationMapper[SympyLikeExpression]):
    # FIXME(pyright): Returning `Any` here is not great, but we would need a big
    # protocol or something if we want it to work for both sympy/symengine.
    @property
    def sym(self) -> Any:
        raise NotImplementedError

    def raise_conversion_error(self, expr: object) -> None:
        raise NotImplementedError

    @override
    def map_variable(self, expr: prim.Variable) -> SympyLikeExpression:
        return self.sym.Symbol(expr.name)

    @override
    def map_constant(self, expr: object) -> SympyLikeExpression:
        return self.sym.sympify(expr)

    @override
    def map_floor_div(self, expr: prim.FloorDiv) -> SympyLikeExpression:
        return self.sym.floor(self.rec(expr.numerator) / self.rec(expr.denominator))

    @override
    def map_call(self, expr: prim.Call) -> SympyLikeExpression:
        if isinstance(expr.function, prim.Variable):
            func_name = expr.function.name
            try:
                func = getattr(self.sym.functions, func_name)
            except AttributeError:
                func = self.sym.Function(func_name)

            return func(*[self.rec(par) for par in expr.parameters])
        else:
            self.raise_conversion_error(expr)
            raise

    @override
    def map_subscript(self, expr: prim.Subscript) -> SympyLikeExpression:
        if isinstance(expr.aggregate, prim.Variable):
            # NOTE: see PymbolicToSympyMapper.map_subscript
            return self.sym.Function("Indexed")(
                expr.aggregate.name,
                *(self.rec(idx) for idx in expr.index_tuple))
        else:
            self.raise_conversion_error(expr)
            raise

    @override
    def map_substitution(self, expr: prim.Substitution) -> SympyLikeExpression:
        return self.sym.Subs(
                self.rec(expr.child),
                tuple([self.sym.Symbol(v) for v in expr.variables]),
                tuple([self.rec(v) for v in expr.values]),
                )

    @override
    def map_if(self, expr: prim.If) -> SympyLikeExpression:
        cond = self.rec(expr.condition)
        return self.sym.Piecewise((self.rec(expr.then), cond),
                                  (self.rec(expr.else_), True))

    @override
    def map_comparison(self, expr: prim.Comparison) -> SympyLikeExpression:
        left = self.rec(expr.left)
        right = self.rec(expr.right)

        if expr.operator == "==":
            return self.sym.Equality(left, right)
        elif expr.operator == "!=":
            return self.sym.Unequality(left, right)  # spellchecker: disable-line  # noqa: E501
        elif expr.operator == "<=":
            return self.sym.LessThan(left, right)
        elif expr.operator == ">=":
            return self.sym.GreaterThan(left, right)
        elif expr.operator == "<":
            return self.sym.StrictLessThan(left, right)
        elif expr.operator == ">":
            return self.sym.StrictGreaterThan(left, right)
        else:
            raise NotImplementedError(f"Unknown operator '{expr.operator}'")

    @override
    def map_derivative(self, expr: prim.Derivative) -> SympyLikeExpression:
        return self.sym.Derivative(self.rec(expr.child),
                *[self.sym.Symbol(v) for v in expr.variables])

# }}}

# vim: fdm=marker
