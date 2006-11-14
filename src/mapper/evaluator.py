import pymbolic.mapper




class UnknownVariableError(Exception):
    pass




class EvaluationMapper(pymbolic.mapper.Mapper):
    def __init__(self, context={}):
        self.Context = context

    def map_constant(self, expr):
        return expr

    def map_variable(self, expr):
        try:
            return self.Context[expr.name]
        except KeyError:
            raise UnknownVariableError, expr.name

    def map_call(self, expr):
        return self(expr.function)(*[self(par) for par in expr.parameters])

    def map_subscript(self, expr):
        return self(expr.aggregate)[self(expr.index)]

    def map_lookup(self, expr):
        return getattr(self(expr.aggregate), expr.name)

    def map_negation(self, expr):
        return -self(expr.child)

    def map_sum(self, expr):
        return sum(self(child) for child in expr.children)

    def map_product(self, expr):
        if len(expr.children) == 0:
            return 1 # FIXME?
        result = self(expr.children[0])
        for child in expr.children[1:]:
            result *= self(child)
        return result

    def map_rational(self, expr):
        return self(expr.numerator) / self(expr.denominator)

    def map_power(self, expr):
        return self(expr.base) ** self(expr.exponent)

    def map_polynomial(self, expr):
        raise NotImplementedError

    def map_list(self, expr):
        return [self(child) for child in expr.Children]




def evaluate(expression, context={}):
    return EvaluationMapper(context)(expression)
    
