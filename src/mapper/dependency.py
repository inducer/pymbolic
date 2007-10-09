from pymbolic.mapper import CombineMapper




class DependencyMapper(CombineMapper):
    def __init__(self, 
            include_subscripts=True, 
            include_lookups=True,
            include_calls=True,
            composite_leaves=None):

        if composite_leaves == False:
            include_subscripts = False
            include_lookups = False
            include_calls = False
        if composite_leaves == True:
            include_subscripts = True
            include_lookups = True
            include_calls = True

        self.IncludeSubscripts = include_subscripts
        self.IncludeLookups = include_lookups
        self.IncludeCalls = include_calls

    def combine(self, values):
        import operator
        return reduce(operator.or_, values, set())

    def handle_unsupported_expression(self, expr, *args, **kwargs):
        return set([expr])

    def map_constant(self, expr):
        return set()

    def map_variable(self, expr):
        return set([expr])

    def map_call(self, expr):
        if self.IncludeCalls:
            return set([expr])
        else:
            return CombineMapper.map_call(self, expr)

    def map_lookup(self, expr):
        if self.IncludeLookups:
            return set([expr])
        else:
            return CombineMapper.map_lookup(self, expr)

    def map_subscript(self, expr):
        if self.IncludeSubscripts:
            return set([expr])
        else:
            return CombineMapper.map_subscript(self, expr)





def get_dependencies(expr, **kwargs):
    return DependencyMapper(**kwargs)(expr)




def is_constant(expr, with_respect_to=None, **kwargs):
    if not with_respect_to:
        return not bool(get_dependencies(expr, **kwargs))
    else:
        return not (set(with_respect_to) & get_dependencies(expr, **kwargs))

