import sets
import pymbolic.mapper




class DependencyMapper(pymbolic.mapper.CombineMapper):
    def combine(self, values):
        import operator
        return reduce(operator.or_, values)

    def map_constant(self, expr):
        return sets.Set()

    def map_variable(self, expr):
        return sets.Set([expr])




def get_dependencies(expr):
    return DependencyMapper()(expr)




def is_constant(expr, with_respect_to=None):
    if not with_respect_to:
        return not bool(get_dependencies(expr))
    else:
        return not (sets.Set(with_respect_to) and get_dependencies(expr))

