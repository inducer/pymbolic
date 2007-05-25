from __future__ import division
from pymbolic.mapper import RecursiveMapper




class UnknownVariableError(Exception):
    pass




class EvaluationMapper(RecursiveMapper):
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

    def map_quotient(self, expr):
        return pymbolic.quotient(self.rec(expr.numerator), self.rec(expr.denominator))

    def map_power(self, expr):
        return self.rec(expr.base) ** self.rec(expr.exponent)

    def map_polynomial(self, expr):
        import pymbolic
        return pymbolic.sum(
                self.rec(coeff)*self.rec(expr.base)**exp
                for exp,coeff in expr.data)

    def map_list(self, expr):
        return [self.rec(child) for child in expr.Children]




class FloatEvaluationMapper(EvaluationMapper):
    def map_constant(self, expr):
        return float(expr)

    def map_rational(self, expr):
        return self.rec(expr.numerator) / self.rec(expr.denominator)




def evaluate(expression, context={}):
    return EvaluationMapper(context)(expression)

def evaluate_kw(expression, **context):
    return EvaluationMapper(context)(expression)

def evaluate_to_float(expression, context={}):
    return FloatEvaluationMapper(context)(expression)
    
    
