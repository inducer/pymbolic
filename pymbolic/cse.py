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

from typing import TYPE_CHECKING, cast

from typing_extensions import Self, override

import pymbolic.primitives as prim
from pymbolic.mapper import IdentityMapper, P, WalkMapper


if TYPE_CHECKING:
    from collections.abc import Callable, Hashable, Iterable, Sequence, Set

    from pymbolic.typing import Expression


COMMUTATIVE_CLASSES = (prim.Sum, prim.Product)


class NormalizedKeyGetter:
    def __call__(self, expr: object, /) -> Hashable:
        if isinstance(expr, COMMUTATIVE_CLASSES):
            kid_count: dict[Expression, int] = {}
            for child in expr.children:
                kid_count[child] = kid_count.get(child, 0) + 1

            return type(expr), frozenset(kid_count.items())
        else:
            return expr


class UseCountMapper(WalkMapper[P]):
    subexpr_counts: dict[Hashable, int]
    get_key: Callable[[object], Hashable]

    def __init__(self, get_key: Callable[[object], Hashable]) -> None:
        self.subexpr_counts = {}
        self.get_key = get_key

    @override
    def visit(self, expr: object, /, *args: P.args, **kwargs: P.kwargs) -> bool:
        key = self.get_key(expr)

        if key in self.subexpr_counts:
            self.subexpr_counts[key] += 1

            # do not re-traverse (and thus re-count subexpressions)
            return False
        else:
            self.subexpr_counts[key] = 1

            # continue traversing
            return True

    @override
    def map_common_subexpression(self, expr: prim.CommonSubexpression, /,
                                 *args: P.args, **kwargs: P.kwargs) -> None:
        # For existing CSEs, reuse has already been decided.
        # Add to

        key = self.get_key(expr)
        if key in self.subexpr_counts:
            self.subexpr_counts[key] += 1
        else:
            # This order reversal matters: Since get_key removes the outer
            # CSE, need to traverse first, then add to counter.

            self.rec(expr.child, *args, **kwargs)
            self.subexpr_counts[key] = 1


class CSEMapper(IdentityMapper[[]]):
    to_eliminate: Set[Hashable]
    get_key: Callable[[object], Hashable]
    canonical_subexprs: dict[Hashable, Expression]

    def __init__(self,
                 to_eliminate: Set[Hashable],
                 get_key: Callable[[object], Hashable]) -> None:
        self.to_eliminate = to_eliminate
        self.get_key = get_key
        self.canonical_subexprs = {}

    def get_cse(self, expr: prim.ExpressionNode, /, key: Hashable = None) -> Expression:
        if key is None:
            key = self.get_key(expr)

        try:
            return self.canonical_subexprs[key]
        except KeyError:
            new_expr = cast("Expression", prim.make_common_subexpression(
                    getattr(IdentityMapper, expr.mapper_method)(self, expr)
                    ))
            self.canonical_subexprs[key] = new_expr
            return new_expr

    @override
    def map_sum(self,
                expr: (prim.Sum | prim.Product | prim.Power
                    | prim.Quotient | prim.Remainder | prim.FloorDiv
                    | prim.Call
                ), /
            ) -> Expression:
        key = self.get_key(expr)
        if key in self.to_eliminate:
            result = self.get_cse(expr, key)
            return result
        else:
            return getattr(IdentityMapper, expr.mapper_method)(self, expr)

    map_product: Callable[[Self, prim.Product], Expression] = map_sum
    map_power: Callable[[Self, prim.Power], Expression] = map_sum
    map_quotient: Callable[[Self, prim.Quotient], Expression] = map_sum
    map_remainder: Callable[[Self, prim.Remainder], Expression] = map_sum
    map_floor_div: Callable[[Self, prim.FloorDiv], Expression] = map_sum
    map_call: Callable[[Self, prim.Call], Expression] = map_sum

    @override
    def map_common_subexpression(self, expr: prim.CommonSubexpression, /) -> Expression:
        # Avoid creating CSE(CSE(...))
        if type(expr) is prim.CommonSubexpression:
            return prim.make_common_subexpression(
                self.rec(expr.child), expr.prefix, expr.scope
                )
        else:
            # expr is of a derived CSE type
            result = self.rec(expr.child)
            if type(result) is prim.CommonSubexpression:
                result = result.child

            return type(expr)(result, expr.prefix, expr.scope,
                              **expr.get_extra_properties())

    @override
    def map_substitution(self, expr: prim.Substitution, /) -> Expression:
        return type(expr)(
                expr.child,
                expr.variables,
                tuple([self.rec(v) for v in expr.values]))


def tag_common_subexpressions(exprs: Iterable[Expression]) -> Sequence[Expression]:
    get_key = NormalizedKeyGetter()
    ucm = UseCountMapper(get_key)

    if isinstance(exprs, prim.ExpressionNode):
        raise TypeError("exprs should be an iterable of expressions")

    for expr in exprs:
        ucm(expr)

    to_eliminate = {subexpr_key
        for subexpr_key, count in ucm.subexpr_counts.items()
        if count > 1}

    cse_mapper = CSEMapper(to_eliminate, get_key)
    result = [cse_mapper(expr) for expr in exprs]
    return result
