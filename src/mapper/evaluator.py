from __future__ import division
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
        return self.rec(expr.function)(*[self.rec(par) for par in expr.parameters])

    def map_subscript(self, expr):
        return self.rec(expr.aggregate)[self.rec(expr.index)]

    def map_lookup(self, expr):
        return getattr(self.rec(expr.aggregate), expr.name)

    def map_negation(self, expr):
        return -self.rec(expr.child)

    def map_sum(self, expr):
        return sum(self.rec(child) for child in expr.children)

    def map_product(self, expr):
        if len(expr.children) == 0:
            return 1 # FIXME?
        result = self.rec(expr.children[0])
        for child in expr.children[1:]:
            result *= self.rec(child)
        return result

    def map_rational(self, expr):
        return self.rec(expr.numerator) / self.rec(expr.denominator)

    def map_power(self, expr):
        return self.rec(expr.base) ** self.rec(expr.exponent)

    def map_polynomial(self, expr):
        return pymbolic.sum(
                coeff*expr.base**exp
                for exp,coeff in expr.data)

    def map_list(self, expr):
        return [self.rec(child) for child in expr.Children]




def evaluate(expression, context={}):
    return EvaluationMapper(context)(expression)
    
