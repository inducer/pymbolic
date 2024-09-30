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

from pymbolic.mapper import (
    CSECachingMapperMixin,
    IdentityMapper,
)


class ConstantFoldingMapperBase:
    def is_constant(self, expr):
        from pymbolic.mapper.dependency import DependencyMapper
        return not bool(DependencyMapper()(expr))

    def evaluate(self, expr):
        from pymbolic import evaluate
        try:
            return evaluate(expr)
        except ValueError:
            return None

    def fold(self, expr, klass, op, constructor):

        constants = []
        nonconstants = []

        queue = list(expr.children)
        while queue:
            child = self.rec(queue.pop(0))  # pylint:disable=no-member
            if isinstance(child, klass):
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

    def map_sum(self, expr):
        import operator

        from pymbolic.primitives import Sum, flattened_sum

        return self.fold(expr, Sum, operator.add, flattened_sum)


class CommutativeConstantFoldingMapperBase(ConstantFoldingMapperBase):
    def map_product(self, expr):
        import operator

        from pymbolic.primitives import Product, flattened_product

        return self.fold(expr, Product, operator.mul, flattened_product)


class ConstantFoldingMapper(
        CSECachingMapperMixin,
        ConstantFoldingMapperBase,
        IdentityMapper):

    map_common_subexpression_uncached = \
            IdentityMapper.map_common_subexpression


# Yes, map_product incompatible: missing *args, **kwargs
class CommutativeConstantFoldingMapper(    # type: ignore[misc]
        CSECachingMapperMixin,
        CommutativeConstantFoldingMapperBase,
        IdentityMapper):

    map_common_subexpression_uncached = \
            IdentityMapper.map_common_subexpression
