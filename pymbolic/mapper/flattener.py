from pymbolic.mapper import IdentityMapper




class FlattenMapper(IdentityMapper):
    def map_sum(self, expr):
        from pymbolic.primitives import flattened_sum
        return flattened_sum(self.rec(ch) for ch in expr.children)

    def map_product(self, expr):
        from pymbolic.primitives import flattened_product
        return flattened_product(self.rec(ch) for ch in expr.children)




def flatten(expr):
    return FlattenMapper()(expr)
