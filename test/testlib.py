__copyright__ = "Copyright (C) 2022 Kaushik Kulkarni"

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


import numpy as np

import pymbolic.primitives as prim
from dataclasses import dataclass, replace
from pytools import UniqueNameGenerator
from pymbolic.mapper import IdentityMapper, CachedIdentityMapper


@dataclass(frozen=True, eq=True)
class RandomExpressionGeneratorContext:
    rng: np.random.Generator
    vng: UniqueNameGenerator
    current_depth: int
    max_depth: int

    def with_increased_depth(self):
        return replace(self, current_depth=self.current_depth+1)


def _generate_random_expr_inner(
        context: RandomExpressionGeneratorContext) -> prim.Expression:

    if context.current_depth >= context.max_depth:
        # force expression to be a leaf type
        return context.rng.integers(0, 42)

    bucket = context.rng.integers(0, 100) / 100.0

    # {{{ set some distribution of expression types

    # 'weight' is proportional to the probability of seeing an expression type
    weights = [1, 1, 1, 1, 1]
    expr_types = [prim.Variable, prim.Sum, prim.Product, prim.Quotient,
                  prim.Call]
    assert len(weights) == len(expr_types)

    # }}}

    buckets = np.cumsum(weights, dtype="float64")/np.sum(weights)

    expr_type = expr_types[np.searchsorted(buckets, bucket)]

    if expr_type == prim.Variable:
        return prim.Variable(context.vng("x"))
    elif expr_type in [prim.Sum, prim.Product]:
        left = _generate_random_expr_inner(context.with_increased_depth())
        right = _generate_random_expr_inner(context.with_increased_depth())
        return expr_type((left, right))
    elif expr_type == prim.Quotient:
        num = _generate_random_expr_inner(context.with_increased_depth())
        den = _generate_random_expr_inner(context.with_increased_depth())
        return prim.Quotient(num, den)
    elif expr_type == prim.Quotient:
        num = _generate_random_expr_inner(context.with_increased_depth())
        den = _generate_random_expr_inner(context.with_increased_depth())
        return prim.Quotient(num, den)
    elif expr_type == prim.Call:
        nargs = 3
        return prim.Variable(context.vng("f"))(
            *[_generate_random_expr_inner(context.with_increased_depth())
              for _ in range(nargs)])
    else:
        raise NotImplementedError(expr_type)


def generate_random_expression(seed: int, max_depth: int = 8) -> prim.Expression:
    from numpy.random import default_rng
    rng = default_rng(seed)
    vng = UniqueNameGenerator()

    context = RandomExpressionGeneratorContext(rng,
                                               vng=vng,
                                               max_depth=max_depth,
                                               current_depth=0)

    return _generate_random_expr_inner(context)


# {{{ custom mappers for tests

class _AlwaysFlatteningMixin:
    def map_sum(self, expr, *args, **kwargs):
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        from pymbolic.primitives import flattened_sum
        return flattened_sum(children)

    def map_product(self, expr, *args, **kwargs):
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        from pymbolic.primitives import flattened_product
        return flattened_product(children)


class AlwaysFlatteningIdentityMapper(_AlwaysFlatteningMixin,
                                     IdentityMapper):
    pass


class AlwaysFlatteningCachedIdentityMapper(_AlwaysFlatteningMixin,
                                           CachedIdentityMapper):
    pass

# }}}
