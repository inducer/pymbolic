import pymbolic.mapper




class DependencyMapper(pymbolic.mapper.CombineMapper):
    def combine(self, values):
        import operator
        return reduce(operator.or_, values)

    def map_constant(self, expr):
        return set()

    def map_variable(self, expr):
        return set([expr])




def get_dependencies(expr):
    return DependencyMapper()(expr)




def is_constant(expr, with_respect_to=None):
    if not with_respect_to:
        return not bool(get_dependencies(expr))
    else:
        return not (set(with_respect_to) & get_dependencies(expr))

