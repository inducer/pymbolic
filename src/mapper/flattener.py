from pymbolic.mapper import IdentityMapper




class FlattenMapper(IdentityMapper):
    def map_sum(self, expr):
        from pymbolic.primitives import flattened_sum
        return flattened_sum(expr.children)

    def map_product(self, expr):
        from pymbolic.primitives import flattened_product
        return flattened_product(expr.children)

    def handle_unsupported_expression(self, expr):
        return expr



def flatten(expr):
    return FlattenMapper()(expr)
