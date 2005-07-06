import sets
import operator

import pymbolic.mapper




class DependencyMapper(pymbolic.mapper.CombineMapper):
    def combine(self, values):
        return reduce(operator.or_, values)

    def map_constant(self, expr):
        return sets.Set()

    def map_variable(self, expr):
        return sets.Set([expr])

    map_subscript = map_variable




def get_dependencies(expr):
    return expr.invoke_mapper(DependencyMapper())




def is_constant(expr, with_respect_to=None):
    return sets.Set(with_respect_to) <= get_dependencies(expr)

