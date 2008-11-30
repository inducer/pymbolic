from pymbolic.mapper import CombineMapper




class DependencyMapper(CombineMapper):
    def __init__(self, 
            include_subscripts=True, 
            include_lookups=True,
            include_calls=True,
            include_cses=False,
            composite_leaves=None):

        if composite_leaves == False:
            include_subscripts = False
            include_lookups = False
            include_calls = False
        if composite_leaves == True:
            include_subscripts = True
            include_lookups = True
            include_calls = True

        self.include_subscripts = include_subscripts
        self.include_lookups = include_lookups
        self.include_calls = include_calls

        self.include_cses = include_cses

    def combine(self, values):
        import operator
        return reduce(operator.or_, values, set())

    def handle_unsupported_expression(self, expr):
        from pymbolic.primitives import AlgebraicLeaf
        if isinstance(expr, AlgebraicLeaf):
            return set([expr])
        else:
            CombineMapper.handle_unsupported_expression(self, expr)

    def map_constant(self, expr):
        return set()

    def map_variable(self, expr):
        return set([expr])

    def map_call(self, expr):
        if self.include_calls:
            return set([expr])
        else:
            return CombineMapper.map_call(self, expr)

    def map_lookup(self, expr):
        if self.include_lookups:
            return set([expr])
        else:
            return CombineMapper.map_lookup(self, expr)

    def map_subscript(self, expr):
        if self.include_subscripts:
            return set([expr])
        else:
            return CombineMapper.map_subscript(self, expr)

    def map_common_subexpression(self, expr):
        if self.include_cses:
            return set([expr])
        else:
            return CombineMapper.map_common_subexpression(self, expr)





def get_dependencies(expr, **kwargs):
    return DependencyMapper(**kwargs)(expr)




def is_constant(expr, with_respect_to=None, **kwargs):
    if not with_respect_to:
        return not bool(get_dependencies(expr, **kwargs))
    else:
        return not (set(with_respect_to) & get_dependencies(expr, **kwargs))

