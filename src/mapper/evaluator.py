class EvaluationMapper:
    def __init__(self, context={}):
        self.Context = context

    def map_constant(self, expr):
        return expr.value

    def map_variable(self, expr):
        return self.Context[expr.name]

    def map_call(self, expr):
        return expr.function.invoke_mapper(self)(
            *[par.invoke_mapper(self)
              for par in expr.parameters])

    def map_subscript(self, expr):
        return expr.aggregate.invoke_mapper(self)[expr.index.invoke_mapper(self)]

    def map_negation(self, expr):
        return -expr.child.invoke_mapper(self)

    def map_sum(self, expr):
        return sum(child.invoke_mapper(self)
                   for child in expr.children)

    def map_product(self, expr):
        if len(expr.children) == 0:
            return 1
        result = expr.children[0].invoke_mapper(self)
        for child in expr.children[1:]:
            result *= child.invoke_mapper(self)
        return result

    def map_rational(self, expr):
        return expr.numerator.invoke_mapper(self) / expr.denominator.invoke_mapper(self)

    def map_power(self, expr):
        return expr.base.invoke_mapper(self) ** expr.exponent.invoke_mapper(self)

    def map_polynomial(self, expr):
        raise NotImplementedError

    def map_list(self, expr):
        return [child.invoke_mapper(self) for child in expr.Children]




def evaluate(expression, context={}):
    return expression.invoke_mapper(EvaluationMapper(context))
    
