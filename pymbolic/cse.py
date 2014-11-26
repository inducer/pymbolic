from __future__ import division
from __future__ import absolute_import
import six

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

import pymbolic.primitives as prim
from pymbolic.mapper import IdentityMapper, WalkMapper

COMMUTATIVE_CLASSES = (prim.Sum, prim.Product)




class NormalizedKeyGetter(object):
    def __call__(self, expr):
        if isinstance(expr, COMMUTATIVE_CLASSES):
            kid_count = {}
            for child in expr.children:
                kid_count[child] = kid_count.get(child, 0) + 1

            return type(expr), frozenset(six.iteritems(kid_count))
        else:
            return expr




class UseCountMapper(WalkMapper):
    def __init__(self, get_key):
        self.subexpr_counts = {}
        self.get_key = get_key

    def visit(self, expr):
        key = self.get_key(expr)

        if key in self.subexpr_counts:
            self.subexpr_counts[key] += 1

            # do not re-traverse (and thus re-count subexpressions)
            return False
        else:
            self.subexpr_counts[key] = 1

            # continue traversing
            return True

    def map_common_subexpression(self, expr, *args, **kwargs):
        # For existing CSEs, reuse has already been decided.
        # Add to

        key = self.get_key(expr)
        if key in self.subexpr_counts:
            self.subexpr_counts[key] += 1
        else:
            # This order reversal matters: Since get_key removes the outer
            # CSE, need to traverse first, then add to counter.

            self.rec(expr.child)
            self.subexpr_counts[key] = 1





class CSEMapper(IdentityMapper):
    def __init__(self, to_eliminate, get_key):
        self.to_eliminate = to_eliminate
        self.get_key = get_key

        self.canonical_subexprs = {}

    def get_cse(self, expr, key=None):
        if key is None:
            key = self.get_key(expr)

        try:
            return self.canonical_subexprs[key]
        except KeyError:
            new_expr = prim.wrap_in_cse(
                    getattr(IdentityMapper, expr.mapper_method)(self, expr))
            self.canonical_subexprs[key] = new_expr
            return new_expr

    def map_sum(self, expr):
        key = self.get_key(expr)
        if key in self.to_eliminate:
            result = self.get_cse(expr, key)
            return result
        else:
            return getattr(IdentityMapper, expr.mapper_method)(self, expr)

    map_product = map_sum
    map_power = map_sum
    map_quotient = map_sum
    map_remainder = map_sum
    map_floor_div = map_sum
    map_call = map_sum

    def map_common_subexpression(self, expr):
        # Avoid creating CSE(CSE(...))
        if type(expr) is prim.CommonSubexpression:
            return prim.wrap_in_cse(self.rec(expr.child), expr.prefix)
        else:
            # expr is of a derived CSE type
            result = self.rec(expr.child)
            if type(result) is prim.CommonSubexpression:
                result = result.child

            return type(expr)(result, expr.prefix, **expr.get_extra_properties())

    def map_substitution(self, expr):
        return type(expr)(
                expr.child,
                expr.variables,
                tuple(self.rec(v) for v in expr.values))




def tag_common_subexpressions(exprs):
    get_key = NormalizedKeyGetter()
    ucm = UseCountMapper(get_key)

    if isinstance(exprs, prim.Expression):
        raise TypeError("exprs should be an iterable of expressions")

    for expr in exprs:
        ucm(expr)

    to_eliminate = set([subexpr_key
        for subexpr_key, count in six.iteritems(ucm.subexpr_counts)
        if count > 1])

    cse_mapper = CSEMapper(to_eliminate, get_key)
    result = [cse_mapper(expr) for expr in exprs]
    return result

