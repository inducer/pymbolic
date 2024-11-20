from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import multiset
import numpy as np
from matchpy import Expression as MatchpyExpression

import pymbolic.interop.matchpy as m
import pymbolic.primitives as p
from pymbolic.interop.matchpy.mapper import Mapper as BaseMatchPyMapper
from pymbolic.mapper import Mapper as BasePymMapper
from pymbolic.typing import Scalar as PbScalar


# {{{ to matchpy

class ToMatchpyExpressionMapper(BasePymMapper):
    """
    Mapper to convert instances of :class:`pymbolic.primitives.Expression` to
    :class:`pymbolic.interop.matchpy.PymbolicOperation`.
    """
    def map_constant(self, expr: Any) -> m.Scalar:
        if np.isscalar(expr):
            return m.Scalar(expr)

        raise NotImplementedError(expr)

    def map_variable(self, expr: p.Variable) -> m.Variable:
        return m.Variable(m.Id(expr.name))

    def map_call(self, expr: p.Call) -> m.Call:
        return m.Call(self.rec(expr.function),
                      m.TupleOp(tuple(self.rec(p)
                                      for p in expr.parameters)))

    def map_subscript(self, expr: p.Subscript) -> m.Subscript:
        return m.Subscript(self.rec(expr.aggregate),
                           m.TupleOp(tuple(self.rec(idx)
                                           for idx in expr.index_tuple)))

    def map_sum(self, expr: p.Sum) -> m.Sum:
        return m.Sum(*[self.rec(child)
                       for child in expr.children])

    def map_product(self, expr: p.Product) -> m.Product:
        return m.Product(*[self.rec(child)
                           for child in expr.children])

    def map_quotient(self, expr: p.Quotient) -> m.TrueDiv:
        return m.TrueDiv(self.rec(expr.numerator), self.rec(expr.denominator))

    def map_floor_div(self, expr: p.FloorDiv) -> m.FloorDiv:
        return m.FloorDiv(self.rec(expr.numerator), self.rec(expr.denominator))

    def map_remainder(self, expr: p.Remainder) -> m.Modulo:
        return m.Modulo(self.rec(expr.numerator), self.rec(expr.denominator))

    def map_power(self, expr: p.Power) -> m.Power:
        return m.Power(self.rec(expr.base), self.rec(expr.exponent))

    def map_left_shift(self, expr: p.LeftShift) -> m.LeftShift:
        return m.LeftShift(self.rec(expr.shiftee), self.rec(expr.shift))

    def map_right_shift(self, expr: p.RightShift) -> m.RightShift:
        return m.RightShift(self.rec(expr.shiftee), self.rec(expr.shift))

    def map_bitwise_not(self, expr: p.BitwiseNot) -> m.BitwiseNot:
        return m.BitwiseNot(self.rec(expr.child))

    def map_bitwise_or(self, expr: p.BitwiseOr) -> m.BitwiseOr:
        return m.BitwiseOr(*[self.rec(child)
                             for child in expr.children])

    def map_bitwise_and(self, expr: p.BitwiseAnd) -> m.BitwiseAnd:
        return m.BitwiseAnd(*[self.rec(child)
                              for child in expr.children])

    def map_bitwise_xor(self, expr: p.BitwiseXor) -> m.BitwiseXor:
        return m.BitwiseXor(*[self.rec(child)
                              for child in expr.children])

    def map_logical_not(self, expr: p.LogicalNot) -> m.LogicalNot:
        return m.LogicalNot(self.rec(expr.child))

    def map_logical_or(self, expr: p.LogicalOr) -> m.LogicalOr:
        return m.LogicalOr(*[self.rec(child)
                             for child in expr.children])

    def map_logical_and(self, expr: p.LogicalAnd) -> m.LogicalAnd:
        return m.LogicalAnd(*[self.rec(child)
                              for child in expr.children])

    def map_comparison(self, expr: p.Comparison) -> m.Comparison:
        # pylint: disable=too-many-function-args
        return m.Comparison(self.rec(expr.left),
                            m.ComparisonOp(expr.operator),
                            self.rec(expr.right),
                            )

    def map_if(self, expr: p.If) -> m.If:
        # pylint: disable=too-many-function-args
        return m.If(self.rec(expr.condition),
                    self.rec(expr.then),
                    self.rec(expr.else_))

    def map_dot_wildcard(self, expr: p.DotWildcard) -> m.Wildcard:
        return m.Wildcard.dot(expr.name)

    def map_star_wildcard(self, expr: p.StarWildcard) -> m.Wildcard:
        return m.Wildcard.star(expr.name)

# }}}


# {{{ from matchpy

class FromMatchpyExpressionMapper(BaseMatchPyMapper):
    def map_scalar(self, expr: m.Scalar) -> PbScalar:
        return expr.value

    def map_variable(self, expr: m.Variable) -> p.Variable:
        return p.Variable(expr.id.value)

    def map_call(self, expr: m.Call) -> p.Call:
        return p.Call(self.rec(expr.function),
                      tuple(self.rec(arg)
                            for arg in expr.args._operands))

    def map_subscript(self, expr: m.Subscript) -> p.Subscript:
        return p.Subscript(self.rec(expr.aggregate),
                           tuple(self.rec(idx)
                                 for idx in expr.indices))

    def map_true_div(self, expr: m.TrueDiv) -> p.Quotient:
        return p.Quotient(self.rec(expr.x1), self.rec(expr.x2))

    def map_floor_div(self, expr: m.FloorDiv) -> p.FloorDiv:
        return p.FloorDiv(self.rec(expr.x1), self.rec(expr.x2))

    def map_modulo(self, expr: m.Modulo) -> p.Remainder:
        return p.Remainder(self.rec(expr.x1), self.rec(expr.x2))

    def map_power(self, expr: m.Power) -> p.Power:
        return p.Power(self.rec(expr.x1), self.rec(expr.x2))

    def map_left_shift(self, expr: m.LeftShift) -> p.LeftShift:
        return p.LeftShift(self.rec(expr.x1), self.rec(expr.x2))

    def map_right_shift(self, expr: m.RightShift) -> p.RightShift:
        return p.RightShift(self.rec(expr.x1), self.rec(expr.x2))

    def map_sum(self, expr: m.Sum) -> p.Sum:
        return p.Sum(tuple(self.rec(child)
                           for child in expr.children))

    def map_product(self, expr: m.Product) -> p.Product:
        return p.Product(tuple(self.rec(operand)
                               for operand in expr.operands))

    def map_logical_or(self, expr: m.LogicalOr) -> p.LogicalOr:
        return p.LogicalOr(tuple(self.rec(operand)
                                 for operand in expr.operands))

    def map_logical_and(self, expr: m.LogicalAnd) -> p.LogicalAnd:
        return p.LogicalAnd(tuple(self.rec(operand)
                                  for operand in expr.operands))

    def map_bitwise_or(self, expr: m.BitwiseOr) -> p.BitwiseOr:
        return p.BitwiseOr(tuple(self.rec(operand)
                                 for operand in expr.operands))

    def map_bitwise_and(self, expr: m.BitwiseAnd) -> p.BitwiseAnd:
        return p.BitwiseAnd(tuple(self.rec(operand)
                                  for operand in expr.operands))

    def map_bitwise_xor(self, expr: m.BitwiseXor) -> p.BitwiseXor:
        return p.BitwiseXor(tuple(self.rec(operand)
                                  for operand in expr.operands))

    def map_logical_not(self, expr: m.LogicalNot) -> p.LogicalNot:
        return p.LogicalNot(self.rec(expr.x))

    def map_bitwise_not(self, expr: m.BitwiseNot) -> p.BitwiseNot:
        return p.BitwiseNot(self.rec(expr.x))

    def map_comparison(self, expr: m.Comparison) -> p.Comparison:
        return p.Comparison(self.rec(expr.left),
                            expr.operator.value,
                            self.rec(expr.right))

    def map_if(self, expr: m.If) -> p.If:
        return p.If(self.rec(expr.condition),
                    self.rec(expr.then),
                    self.rec(expr.else_))

# }}}


@dataclass(frozen=True, eq=True)
class ToFromReplacement:
    f: Callable[..., p.ExpressionNode]
    to_matchpy_expr: m.ToMatchpyT
    from_matchpy_expr: m.FromMatchpyT

    def __call__(self, **kwargs):
        kwargs_to_f = {}

        for kw, arg in kwargs.items():
            if isinstance(arg, MatchpyExpression):
                arg = self.from_matchpy_expr(arg)
            elif isinstance(arg, multiset.Multiset):
                arg = multiset.Multiset({self.from_matchpy_expr(expr): count
                                         for expr, count in arg.items()})
            elif isinstance(arg, tuple):
                arg = tuple(self.from_matchpy_expr(el) for el in arg)
            else:
                raise NotImplementedError(f"Cannot convert back {type(arg)}")

            kwargs_to_f[kw] = arg

        return self.to_matchpy_expr(self.f(**kwargs_to_f))

# vim: foldmethod=marker
