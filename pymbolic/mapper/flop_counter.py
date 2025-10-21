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

from typing import TYPE_CHECKING

from typing_extensions import override

import pymbolic.primitives as p
from pymbolic.mapper import CachedMapper, CombineMapper
from pymbolic.typing import ArithmeticExpression


if TYPE_CHECKING:
    from collections.abc import Iterable


class FlopCounterBase(CombineMapper[ArithmeticExpression, []]):
    @override
    def combine(self, values: Iterable[ArithmeticExpression]) -> ArithmeticExpression:
        return sum(values)

    @override
    def map_constant(self, expr: object) -> ArithmeticExpression:
        return 0

    @override
    def map_variable(self, expr: p.Variable) -> ArithmeticExpression:
        return 0

    @override
    def map_sum(self, expr: p.Sum | p.Product) -> ArithmeticExpression:
        if expr.children:
            return len(expr.children) - 1 + sum(self.rec(ch) for ch in expr.children)
        else:
            return 0

    map_product = map_sum

    @override
    def map_quotient(self, expr: p.Quotient | p.FloorDiv) -> ArithmeticExpression:
        return 1 + self.rec(expr.numerator) + self.rec(expr.denominator)

    map_floor_div = map_quotient

    @override
    def map_power(self, expr: p.Power) -> ArithmeticExpression:
        return 1 + self.rec(expr.base) + self.rec(expr.exponent)

    @override
    def map_if(self, expr: p.If) -> ArithmeticExpression:
        rec_then = self.rec(expr.then)
        rec_else = self.rec(expr.else_)
        if isinstance(rec_then, int) and isinstance(rec_else, int):
            eval_flops = max(rec_then, rec_else)
        else:
            eval_flops = p.Max((rec_then, rec_else))
        return self.rec(expr.condition) + eval_flops


class FlopCounter(CachedMapper[int, []], FlopCounterBase):  # pyright: ignore[reportGeneralTypeIssues]
    pass


class CSEAwareFlopCounter(FlopCounterBase):
    """A flop counter that only counts the contribution from common
    subexpressions once.

    .. warning::

        You must use a fresh mapper for each new evaluation operation for which
        reuse may take place.
    """
    def __init__(self):
        super().__init__()
        self.cse_seen_set: set[p.CommonSubexpression] = set()

    @override
    def map_common_subexpression(self,
                expr: p.CommonSubexpression
            ) -> ArithmeticExpression:
        if expr in self.cse_seen_set:
            return 0
        else:
            self.cse_seen_set.add(expr)
            return self.rec(expr.child)
