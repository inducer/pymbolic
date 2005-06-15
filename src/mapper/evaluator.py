class EvaluationMapper:
    def __init__(self, context={}):
        self.Context = context

    def map_constant(self, expr):
        return expr.Value

    def map_variable(self, expr):
        return self.Context[expr.Name]

    def map_call(self, expr):
        return expr.Function.invoke_mapper(self)(
            *[par.invoke_mapper(self)
              for par in expr.Parameters])

    def map_sum(self, expr):
        return sum(child.invoke_mapper(self)
                   for child in expr.Children)

    def map_negation(self, expr):
        return -expr.Child.invoke_mapper(self)

    def map_product(self, expr):
        if len(expr.Children) == 0:
            return 1
        result = expr.Children[0].invoke_mapper(self)
        for child in expr.Children[1:]:
            result *= child.invoke_mapper(self)
        return result

    def map_quotient(self, expr):
        return expr.Child1.invoke_mapper(self) / expr.Child2.invoke_mapper(self)

    def map_power(self, expr):
        return expr.Child1.invoke_mapper(self) ** expr.Child2.invoke_mapper(self)

    def map_polynomial(self, expr):
        if len(expr.Children) == 0:
            return 0
        result = expr.Children[-1].invoke_mapper(self)
        b_ev = expr.Base.invoke_mapper(self)
        for child in expr.Children[-2::-1]:
            result = result * b_ev + child.invoke_mapper(self)
        return result

    def map_list(self, expr):
        return [child.invoke_mapper(self) for child in expr.Children]




def evaluate(expression, context={}):
    return expression.invoke_mapper(EvaluationMapper(context))
    
