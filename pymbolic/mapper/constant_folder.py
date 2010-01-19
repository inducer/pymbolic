from pymbolic.mapper import \
        IdentityMapper, \
        NonrecursiveIdentityMapper, \
        CSECachingMapperMixin




class ConstantFoldingMapperBase(object):
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
            child = self.rec(queue.pop(0))
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
            constant = reduce(op, constants)
            return constructor(tuple([constant]+nonconstants))
        else:
            return constructor(tuple(nonconstants))

    def map_sum(self, expr):
        from pymbolic.primitives import Sum, flattened_sum
        import operator

        return self.fold(expr, Sum, operator.add, flattened_sum)



class CommutativeConstantFoldingMapperBase(ConstantFoldingMapperBase):
    def map_product(self, expr):
        from pymbolic.primitives import Product, flattened_product
        import operator

        return self.fold(expr, Product, operator.mul, flattened_product)




class ConstantFoldingMapper(
        CSECachingMapperMixin, 
        ConstantFoldingMapperBase, 
        IdentityMapper):

    map_common_subexpression_uncached = \
            IdentityMapper.map_common_subexpression

class NonrecursiveConstantFoldingMapper(
        CSECachingMapperMixin,
        NonrecursiveIdentityMapper, 
        ConstantFoldingMapperBase):

    map_common_subexpression_uncached = \
            NonrecursiveIdentityMapper.map_common_subexpression

class CommutativeConstantFoldingMapper(
        CSECachingMapperMixin,
        CommutativeConstantFoldingMapperBase,
        IdentityMapper):

    map_common_subexpression_uncached = \
            IdentityMapper.map_common_subexpression

class NonrecursiveCommutativeConstantFoldingMapper(
        CSECachingMapperMixin,
        CommutativeConstantFoldingMapperBase,
        NonrecursiveIdentityMapper,):

    map_common_subexpression_uncached = \
            NonrecursiveIdentityMapper.map_common_subexpression

