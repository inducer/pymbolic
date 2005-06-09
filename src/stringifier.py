class StringifyMapper:
    def map_constant(self, expr):
        return str(expr.Value)

    def map_variable(self, expr):
        return expr.Name

    def map_call(self, expr):
        return "%s(%s)" % \
               (expr.Function.invoke_mapper(self),
                ", ".join(i.invoke_mapper(self) for i in expr.Parameters))

    def map_sum(self, expr):
        return "(%s)" % "+".join(i.invoke_mapper(self) for i in expr.Children)

    def map_negation(self, expr):
        return "-%s" % expr.Child.invoke_mapper(self)

    def map_product(self, expr):
        return "(%s)" % "*".join(i.invoke_mapper(self) for i in expr.Children)

    def map_quotient(self, expr):
        return "(%s/%s)" % (expr.Child1.invoke_mapper(self), 
                            expr.Child2.invoke_mapper(self))

    def map_power(self, expr):
        return "(%s**%s)" % (expr.Child1.invoke_mapper(self), 
                            expr.Child2.invoke_mapper(self))

    def map_polynomial(self, expr):
        raise NotImplementedError

    def map_list(self, expr):
        return "[%s]" % ", ".join([i.invoke_mapper(self) for i in expr.Children])




def stringify(expression):
    expression.invoke_mapper(StringifyMapper)
