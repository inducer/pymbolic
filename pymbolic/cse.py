from __future__ import division
import pymbolic.primitives as prim
from pymbolic.mapper import IdentityMapper, WalkMapper

COMMUTATIVE_CLASSES = (prim.Sum, prim.Product)




def get_normalized_cse_key(node):
    if isinstance(node, COMMUTATIVE_CLASSES):
        return type(node), frozenset(node.children)
    else:
        return node




class CSEMapper(IdentityMapper):
    def __init__(self, to_eliminate):
        self.to_eliminate = to_eliminate

        self.canonical_subexprs = {}

    def get_cse(self, expr, key=None):
        if key is None:
            key = get_normalized_cse_key(expr)

        try:
            return self.canonical_subexprs[key]
        except KeyError:
            new_expr = prim.CommonSubexpression(
                    getattr(IdentityMapper, expr.mapper_method)(self, expr))
            self.canonical_subexprs[key] = new_expr
            return new_expr

    def map_sum(self, expr):
        key = get_normalized_cse_key(expr)
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

    def map_quotient(self, expr):
        if expr in self.to_eliminate:
            return self.get_cse(expr)
        else:
            return IdentityMapper.map_quotient(self, expr)

    def map_substitution(self, expr):
        return type(expr)(
                expr.child,
                expr.variables,
                tuple(self.rec(v) for v in expr.values))




class UseCountMapper(WalkMapper):
    def __init__(self):
        self.subexpr_counts = {}

    def visit(self, expr):
        key = get_normalized_cse_key(expr)

        if key in self.subexpr_counts:
            self.subexpr_counts[key] += 1

            # do not re-traverse (and thus re-count subexpressions)
            return False
        else:
            self.subexpr_counts[key] = 1

            # continue traversing
            return True




def tag_common_subexpressions(exprs):
    ucm = UseCountMapper()

    if isinstance(exprs, prim.Expression):
        raise TypeError("exprs should be an iterable of expressions")

    for expr in exprs:
        ucm(expr)

    to_eliminate = set([subexpr_key
        for subexpr_key, count in ucm.subexpr_counts.iteritems()
        if count > 1])
    cse_mapper = CSEMapper(to_eliminate)
    result = [cse_mapper(expr) for expr in exprs]
    return result

