import mapper
import operator




class ConstantDetectionMapper(mapper.CombineMapper):
    def __init__(self, with_respect_to=None):
        self.WRT = with_respect_to

    def combine(self, values):
        return reduce(operator.and_, values)

    def map_constant(self, expr):
        return True

    def map_variable(self, expr):
        if self.WRT:
            return expr.Name not in self.WRT
        else:
            return False



def is_constant(expr, with_respect_to=None):
    return expr.invoke_mapper(ConstantDetectionMapper(with_respect_to))
