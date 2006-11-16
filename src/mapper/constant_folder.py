from pymbolic.mapper import IdentityMapper, NonrecursiveIdentityMapper




class ConstantFoldingMapperBase(object):
    def fold(self, expr, klass, op, constructor):
        from pymbolic import is_constant

        constants = []
        nonconstants = []

        queue = expr.children
        while queue:
            child = self.rec(queue.pop(0))
            if isinstance(child, klass):
                queue = child.children + queue
            else:
                if is_constant(child):
                    constants.append(child)
                else:
                    nonconstants.append(child)

        if constants:
            import operator
            constant = reduce(op, constants)
            return constructor([constant]+nonconstants)
        else:
            return constructor(nonconstants)

    def map_sum(self, expr):
        from pymbolic import sum
        from pymbolic.primitives import Sum
        import operator

        return self.fold(expr, Sum, operator.add, sum)



class CommutativeConstantFoldingMapperBase(ConstantFoldingMapperBase):
    def map_product(self, expr):
        from pymbolic import product
        from pymbolic.primitives import Product
        import operator

        return self.fold(expr, Product, operator.mul, product)




class ConstantFoldingMapper(IdentityMapper, ConstantFoldingMapperBase):
    pass

class NonrecursiveConstantFoldingMapper(
        NonrecursiveIdentityMapper, 
        ConstantFoldingMapperBase):
    pass

class CommutativeConstantFoldingMapper(IdentityMapper, 
        CommutativeConstantFoldingMapperBase):
    pass

class NonrecursiveCommutativeConstantFoldingMapper(
        NonrecursiveIdentityMapper, 
        CommutativeConstantFoldingMapperBase):
    pass

