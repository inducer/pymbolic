class StringifyMapper:
    def map_constant(self, expr):
        return str(expr.value)

    def map_variable(self, expr):
        return expr.name

    def map_call(self, expr):
        return "%s(%s)" % \
               (expr.function.invoke_mapper(self),
                ", ".join(i.invoke_mapper(self) for i in expr.parameters))

    def map_subscript(self, expr):
        return "%s[%s]" % \
               (expr.aggregate.invoke_mapper(self),
                expr.index.invoke_mapper(self))

    def map_negation(self, expr):
        return "-%s" % expr.child.invoke_mapper(self)

    def map_sum(self, expr):
        return "(%s)" % "+".join(i.invoke_mapper(self) for i in expr.children)

    def map_product(self, expr):
        return "(%s)" % "*".join(i.invoke_mapper(self) for i in expr.children)

    def map_rational(self, expr):
        return "(%s/%s)" % (expr.numerator.invoke_mapper(self), 
                            expr.denominator.invoke_mapper(self))

    def map_power(self, expr):
        return "(%s**%s)" % (expr.base.invoke_mapper(self), 
                             expr.exponent.invoke_mapper(self))

    def map_polynomial(self, expr):
        raise NotImplementedError

    def map_list(self, expr):
        return "[%s]" % ", ".join([i.invoke_mapper(self) for i in expr.children])




def stringify(expression):
    expression.invoke_mapper(StringifyMapper)
