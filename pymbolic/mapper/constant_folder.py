"""
.. autoclass:: ConstantFoldingMapperBase
    :show-inheritance:
.. autoclass:: ConstantFoldingMapper
    :show-inheritance:
.. autoclass:: CommutativeConstantFoldingMapperBase
    :show-inheritance:
.. autoclass:: CommutativeConstantFoldingMapper
    :show-inheritance:
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


from typing import TYPE_CHECKING

from typing_extensions import Self, override

import pymbolic.primitives as prim
from pymbolic.mapper import (
    CSECachingMapperMixin,
    IdentityMapper,
    Mapper,
)
from pymbolic.typing import ArithmeticExpression, Expression


if TYPE_CHECKING:
    from collections.abc import Callable


class ConstantFoldingMapperBase(Mapper[Expression, []]):
    def is_constant(self, expr: Expression, /) -> bool:
        from pymbolic.mapper.dependency import DependencyMapper
        return not bool(DependencyMapper()(expr))

    def evaluate(self, expr: Expression, /) -> Expression | None:
        from pymbolic import evaluate

        try:
            return evaluate(expr)
        except ValueError:
            return None

    def fold(self,
             expr: prim.Sum | prim.Product,
             op: Callable[
                 [ArithmeticExpression, ArithmeticExpression],
                 ArithmeticExpression],
             constructor: Callable[
                     [tuple[ArithmeticExpression, ...]],
                     ArithmeticExpression],
         ) -> Expression:
        klass = type(expr)

        constants: list[ArithmeticExpression] = []
        nonconstants: list[ArithmeticExpression] = []

        queue = list(expr.children)
        while queue:
            child = self.rec(queue.pop(0))
            assert prim.is_arithmetic_expression(child)

            if isinstance(child, klass):
                assert isinstance(child, (prim.Sum, prim.Product))
                queue = list(child.children) + queue
            else:
                if self.is_constant(child):
                    value = self.evaluate(child)
                    if value is None:
                        # couldn't evaluate
                        nonconstants.append(child)
                    else:
                        constants.append(value)
                else:
                    nonconstants.append(child)

        if constants:
            from functools import reduce
            constant = reduce(op, constants)
            return constructor((constant, *nonconstants))
        else:
            return constructor(tuple(nonconstants))

    @override
    def map_sum(self, expr: prim.Sum, /) -> Expression:
        import operator

        from pymbolic.primitives import flattened_sum

        return self.fold(expr, operator.add, flattened_sum)


class CommutativeConstantFoldingMapperBase(ConstantFoldingMapperBase):
    @override
    def map_product(self, expr: prim.Product, /) -> Expression:
        import operator

        from pymbolic.primitives import flattened_product

        return self.fold(expr, operator.mul, flattened_product)


class ConstantFoldingMapper(
        CSECachingMapperMixin[Expression, []],
        ConstantFoldingMapperBase,
        IdentityMapper[[]]):

    map_common_subexpression_uncached: (
        Callable[[Self, prim.CommonSubexpression], Expression]) = (
            IdentityMapper.map_common_subexpression)


class CommutativeConstantFoldingMapper(
        CSECachingMapperMixin[Expression, []],
        CommutativeConstantFoldingMapperBase,
        IdentityMapper[[]]):

    map_common_subexpression_uncached: (
        Callable[[Self, prim.CommonSubexpression], Expression]) = (
            IdentityMapper.map_common_subexpression)
