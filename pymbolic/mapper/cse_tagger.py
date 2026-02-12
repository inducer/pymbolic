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

from typing_extensions import Self, override

import pymbolic.primitives as prim
from pymbolic.mapper import IdentityMapper, WalkMapper


if TYPE_CHECKING:
    from collections.abc import Callable, Hashable

    from pymbolic.typing import Expression


class CSEWalkMapper(WalkMapper[[]]):
    subexpr_histogram: dict[Hashable, int]

    def __init__(self) -> None:
        self.subexpr_histogram = {}

    @override
    def visit(self, expr: object) -> bool:
        self.subexpr_histogram[expr] = self.subexpr_histogram.get(expr, 0) + 1
        return True


class CSETagMapper(IdentityMapper[[]]):
    subexpr_histogram: dict[Hashable, int]

    def __init__(self, walk_mapper: CSEWalkMapper) -> None:
        self.subexpr_histogram = walk_mapper.subexpr_histogram

    def _map_subexpr(self, expr: prim.ExpressionNode, /) -> Expression:
        if self.subexpr_histogram.get(expr, 0) > 1:
            return prim.CommonSubexpression(expr, scope=prim.cse_scope.EVALUATION)
        else:
            return getattr(IdentityMapper, expr.mapper_method)(self, expr)

    map_call: Callable[[Self, prim.Call], Expression] = _map_subexpr
    map_sum: Callable[[Self, prim.Sum], Expression] = _map_subexpr
    map_product: Callable[[Self, prim.Product], Expression] = _map_subexpr
    map_quotient: Callable[[Self, prim.Quotient], Expression] = _map_subexpr
    map_floor_div: Callable[[Self, prim.FloorDiv], Expression] = _map_subexpr
    map_remainder: Callable[[Self, prim.Remainder], Expression] = _map_subexpr
    map_power: Callable[[Self, prim.Power], Expression] = _map_subexpr
    map_matmul: Callable[[Self, prim.Matmul], Expression] = _map_subexpr

    map_left_shift: Callable[[Self, prim.LeftShift], Expression] = _map_subexpr
    map_right_shift: Callable[[Self, prim.RightShift], Expression] = _map_subexpr

    map_bitwise_not: Callable[[Self, prim.BitwiseNot], Expression] = _map_subexpr
    map_bitwise_or: Callable[[Self, prim.BitwiseOr], Expression] = _map_subexpr
    map_bitwise_xor: Callable[[Self, prim.BitwiseXor], Expression] = _map_subexpr
    map_bitwise_and: Callable[[Self, prim.BitwiseAnd], Expression] = _map_subexpr

    map_comparison: Callable[[Self, prim.Comparison], Expression] = _map_subexpr

    map_logical_not: Callable[[Self, prim.LogicalNot], Expression] = _map_subexpr
    map_logical_and: Callable[[Self, prim.LogicalAnd], Expression] = _map_subexpr
    map_logical_or: Callable[[Self, prim.LogicalOr], Expression] = _map_subexpr

    map_if: Callable[[Self, prim.If], Expression] = _map_subexpr
    map_if_positive: Callable[[Self, prim.If], Expression] = _map_subexpr
