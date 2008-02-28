from pymbolic.mapper import IdentityMapper, NonrecursiveIdentityMapper




class ConstantFoldingMapperBase(object):
    def fold(self, expr, klass, op, constructor):
        from pymbolic import is_constant, evaluate

        constants = []
        nonconstants = []

        queue = list(expr.children)
        while queue:
            child = self.rec(queue.pop(0))
            if isinstance(child, klass):
                queue = list(child.children) + queue
            else:
                if is_constant(child):
                    constants.append(evaluate(child))
                else:
                    nonconstants.append(child)

        if constants:
            import operator
            constant = reduce(op, constants)
            return constructor(tuple([constant]+nonconstants))
        else:
            return constructor(tuple(nonconstants))

    def map_sum(self, expr):
        from pymbolic.primitives import Sum
        import operator

        return self.fold(expr, Sum, operator.add, Sum)



class CommutativeConstantFoldingMapperBase(ConstantFoldingMapperBase):
    def map_product(self, expr):
        from pymbolic.primitives import Product
        import operator

        return self.fold(expr, Product, operator.mul, Product)




class ConstantFoldingMapper(ConstantFoldingMapperBase, IdentityMapper):
    pass

class NonrecursiveConstantFoldingMapper(
        NonrecursiveIdentityMapper, 
        ConstantFoldingMapperBase):
    pass

class CommutativeConstantFoldingMapper(CommutativeConstantFoldingMapperBase,
        IdentityMapper):
    pass

class NonrecursiveCommutativeConstantFoldingMapper(
        CommutativeConstantFoldingMapperBase,
        NonrecursiveIdentityMapper,):
    pass

