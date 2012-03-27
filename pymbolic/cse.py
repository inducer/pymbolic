from __future__ import division
import pymbolic.primitives as prim
from pymbolic.mapper import IdentityMapper, WalkMapper
from pytools import memoize_method

COMMUTATIVE_CLASSES = (prim.Sum, prim.Product)




class CSERemover(IdentityMapper):
    def map_common_subexpression(self, expr):
        return self.rec(expr.child)




class NormalizedKeyGetter(object):
    def __init__(self):
        self.cse_remover = CSERemover()

    @memoize_method
    def remove_cses(self, expr):
        return self.cse_remover(expr)

    def __call__(self, expr):
        expr = self.remove_cses(expr)
        if isinstance(expr, COMMUTATIVE_CLASSES):
            return type(expr), frozenset(expr.children)
        else:
            return expr




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
        # don't duplicate CSEs
        return prim.wrap_in_cse(self.rec(expr.child), expr.prefix)

    def map_substitution(self, expr):
        return type(expr)(
                expr.child,
                expr.variables,
                tuple(self.rec(v) for v in expr.values))




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




def tag_common_subexpressions(exprs):
    get_key = NormalizedKeyGetter()
    ucm = UseCountMapper(get_key)

    if isinstance(exprs, prim.Expression):
        raise TypeError("exprs should be an iterable of expressions")

    for expr in exprs:
        ucm(expr)

    to_eliminate = set([subexpr_key
        for subexpr_key, count in ucm.subexpr_counts.iteritems()
        if count > 1])
    cse_mapper = CSEMapper(to_eliminate, get_key)
    result = [cse_mapper(expr) for expr in exprs]
    return result

