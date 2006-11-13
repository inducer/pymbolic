PREC_CALL = 5
PREC_POWER = 4
PREC_UNARY = 3
PREC_PRODUCT = 2
PREC_SUM = 1
PREC_NONE = 0



class StringifyMapper:
    def map_constant(self, expr, enclosing_prec):
        return str(expr.value)

    def map_variable(self, expr, enclosing_prec):
        return expr.name

    def map_call(self, expr, enclosing_prec):
        result = "%s(%s)" % \
                (expr.function.invoke_mapper(self, PREC_CALL),
                        ", ".join(i.invoke_mapper(self, PREC_NONE) 
                            for i in expr.parameters))
        if enclosing_prec > PREC_CALL:
            return "(%s)" % result
        else:
            return result

    def map_subscript(self, expr, enclosing_prec):
        result = "%s[%s]" % \
                (expr.aggregate.invoke_mapper(self, PREC_CALL),
                        expr.index.invoke_mapper(self, PREC_CALL))
        if enclosing_prec > PREC_CALL:
            return "(%s)" % result
        else:
            return result

    def map_lookup(self, expr, enclosing_prec):
        result = "%s.%s" % \
               (expr.aggregate.invoke_mapper(self, PREC_CALL), 
                       expr.name)
        if enclosing_prec > PREC_CALL:
            return "(%s)" % result
        else:
            return result

    def map_negation(self, expr, enclosing_prec):
        result = "-%s" % expr.child.invoke_mapper(self, PREC_UNARY)
        if enclosing_prec > PREC_UNARY:
            return "(%s)" % result
        else:
            return result

    def map_sum(self, expr, enclosing_prec):
        result = "+".join(i.invoke_mapper(self, PREC_SUM) for i in expr.children)
        if enclosing_prec > PREC_SUM:
            return "(%s)" % result
        else:
            return result

    def map_product(self, expr, enclosing_prec):
        result = "*".join(i.invoke_mapper(self, PREC_PRODUCT) 
                for i in expr.children)
        if enclosing_prec > PREC_PRODUCT:
            return "(%s)" % result
        else:
            return result

    def map_quotient(self, expr, enclosing_prec):
        result = "%s/%s" % (
                expr.numerator.invoke_mapper(self, PREC_PRODUCT), 
                expr.denominator.invoke_mapper(self, PREC_PRODUCT)
                )
        if enclosing_prec > PREC_PRODUCT:
            return "(%s)" % result
        else:
            return result
    map_rational = map_quotient

    def map_power(self, expr, enclosing_prec):
        result = "%s**%s" % (
                expr.base.invoke_mapper(self, PREC_POWER), 
                expr.exponent.invoke_mapper(self, PREC_POWER)
                )
        if enclosing_prec > PREC_POWER:
            return "(%s)" % result
        else:
            return result

    def map_polynomial(self, expr, enclosing_prec):
        raise NotImplementedError

    def map_list(self, expr, enclosing_prec):
        return "[%s]" % ", ".join([i.invoke_mapper(self) for i in expr.children])
