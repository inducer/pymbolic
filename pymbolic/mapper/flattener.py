"""
.. autoclass:: FlattenMapper

.. currentmodule:: pymbolic

.. autofunction:: flatten
"""

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


import pymbolic.primitives as p
from pymbolic.mapper import IdentityMapper
from pymbolic.typing import ExpressionT


class FlattenMapper(IdentityMapper[[]]):
    """
    Applies :func:`pymbolic.primitives.flattened_sum`
    to :class:`~pymbolic.primitives.Sum`"
    and :func:`pymbolic.primitives.flattened_product`
    to :class:`~pymbolic.primitives.Product`."
    Also applies light-duty simplification to other operators.

    This parallels what was done implicitly in the expression node
    constructors.
    """
    def map_sum(self, expr: p.Sum) -> ExpressionT:
        from pymbolic.primitives import flattened_sum
        return flattened_sum([self.rec(ch) for ch in expr.children])

    def map_product(self, expr: p.Product) -> ExpressionT:
        from pymbolic.primitives import flattened_product
        return flattened_product([self.rec(ch) for ch in expr.children])

    def map_quotient(self, expr: p.Quotient) -> ExpressionT:
        r_num = self.rec(expr.numerator)
        r_den = self.rec(expr.denominator)
        assert p.is_arithmetic_expression(r_den)
        if p.is_zero(r_num):
            return 0
        if p.is_zero(r_den - 1):
            return r_num

        return expr.__class__(r_num, r_den)

    def map_floor_div(self, expr: p.FloorDiv) -> ExpressionT:
        r_num = self.rec(expr.numerator)
        r_den = self.rec(expr.denominator)
        assert p.is_arithmetic_expression(r_den)
        if p.is_zero(r_num):
            return 0
        if p.is_zero(r_den - 1):
            return r_num

        return expr.__class__(r_num, r_den)

    def map_remainder(self, expr: p.Remainder) -> ExpressionT:
        r_num = self.rec(expr.numerator)
        r_den = self.rec(expr.denominator)
        assert p.is_arithmetic_expression(r_den)
        if p.is_zero(r_num):
            return 0
        if p.is_zero(r_den - 1):
            return r_num

        return expr.__class__(r_num, r_den)

    def map_power(self, expr: p.Power) -> ExpressionT:
        r_base = self.rec(expr.base)
        r_exp = self.rec(expr.exponent)

        assert p.is_arithmetic_expression(r_exp)

        if p.is_zero(r_exp - 1):
            return r_base

        return expr.__class__(r_base, r_exp)


def flatten(expr):
    return FlattenMapper()(expr)
