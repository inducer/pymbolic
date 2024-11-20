"""
.. autoclass:: ConstantFoldingMapper
.. autoclass:: CommutativeConstantFoldingMapper
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

from collections.abc import Callable

from pymbolic.mapper import (
    CSECachingMapperMixin,
    IdentityMapper,
    Mapper,
)
from pymbolic.primitives import Product, Sum, is_arithmetic_expression
from pymbolic.typing import ArithmeticExpression, Expression


class ConstantFoldingMapperBase(Mapper[Expression, []]):
    def is_constant(self, expr):
        from pymbolic.mapper.dependency import DependencyMapper
        return not bool(DependencyMapper()(expr))

    def evaluate(self, expr):
        from pymbolic import evaluate
        try:
            return evaluate(expr)
        except ValueError:
            return None

    def fold(self,
             expr: Sum | Product,
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
            assert is_arithmetic_expression(child)

            if isinstance(child, klass):
                assert isinstance(child, Sum | Product)
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

    def map_sum(self, expr: Sum) -> Expression:
        import operator

        from pymbolic.primitives import flattened_sum

        return self.fold(expr, operator.add, flattened_sum)


class CommutativeConstantFoldingMapperBase(ConstantFoldingMapperBase):
    def map_product(self, expr):
        import operator

        from pymbolic.primitives import flattened_product

        return self.fold(expr, operator.mul, flattened_product)


class ConstantFoldingMapper(
        CSECachingMapperMixin[Expression, []],
        ConstantFoldingMapperBase,
        IdentityMapper[[]]):

    map_common_subexpression_uncached = \
            IdentityMapper.map_common_subexpression


class CommutativeConstantFoldingMapper(
        CSECachingMapperMixin[Expression, []],
        CommutativeConstantFoldingMapperBase,
        IdentityMapper[[]]):

    map_common_subexpression_uncached = \
            IdentityMapper.map_common_subexpression
