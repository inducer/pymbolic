import pymbolic.mapper




PREC_CALL = 5
PREC_POWER = 4
PREC_UNARY = 3
PREC_PRODUCT = 2
PREC_SUM = 1
PREC_NONE = 0



class StringifyMapper(pymbolic.mapper.RecursiveMapper):
    def map_constant(self, expr, enclosing_prec):
        return str(expr)

    def map_variable(self, expr, enclosing_prec):
        return expr.name

    def map_call(self, expr, enclosing_prec):
        result = "%s(%s)" % \
                (self.rec(expr.function, PREC_CALL),
                        ", ".join(self.rec(i, PREC_NONE) 
                            for i in expr.parameters))
        if enclosing_prec > PREC_CALL:
            return "(%s)" % result
        else:
            return result

    def map_subscript(self, expr, enclosing_prec):
        result = "%s[%s]" % \
                (self.rec(expr.aggregate, PREC_CALL), self.rec(expr.index, PREC_CALL))
        if enclosing_prec > PREC_CALL:
            return "(%s)" % result
        else:
            return result

    def map_lookup(self, expr, enclosing_prec):
        result = "%s.%s" % (self.rec(expr.aggregate, PREC_CALL), expr.name)
        if enclosing_prec > PREC_CALL:
            return "(%s)" % result
        else:
            return result

    def map_negation(self, expr, enclosing_prec):
        result = "-%s" % self.rec(expr.child, PREC_UNARY)
        if enclosing_prec > PREC_UNARY:
            return "(%s)" % result
        else:
            return result

    def map_sum(self, expr, enclosing_prec):
        result = "+".join(self.rec(i, PREC_SUM) for i in expr.children)
        if enclosing_prec > PREC_SUM:
            return "(%s)" % result
        else:
            return result

    def map_product(self, expr, enclosing_prec):
        result = "*".join(self.rec(i, PREC_PRODUCT) 
                for i in expr.children)
        if enclosing_prec > PREC_PRODUCT:
            return "(%s)" % result
        else:
            return result

    def map_quotient(self, expr, enclosing_prec):
        result = "%s/%s" % (
                self.rec(expr.numerator, PREC_PRODUCT), 
                self.rec(expr.denominator, PREC_PRODUCT)
                )
        if enclosing_prec > PREC_PRODUCT:
            return "(%s)" % result
        else:
            return result

    def map_power(self, expr, enclosing_prec):
        result = "%s**%s" % (
                self.rec(expr.base, PREC_POWER), 
                self.rec(expr.exponent, PREC_POWER)
                )
        if enclosing_prec > PREC_POWER:
            return "(%s)" % result
        else:
            return result

    def map_polynomial(self, expr, enclosing_prec):
        sbase = str(expr.base)
        def stringify_expcoeff((exp, coeff)):
            if exp == 1:
                if not (coeff-1):
                    return sbase
                else:
                    return "%s*%s" % (str(coeff), sbase)
            elif exp == 0:
                return str(coeff)
            else:
                if not (coeff-1):
                    return "%s**%s" % (sbase, exp) 
                else:
                    return "%s*%s**%s" % (str(coeff), sbase, exp) 

        result = "%s" % " + ".join(stringify_expcoeff(i) for i in expr.data[::-1])
        if enclosing_prec > PREC_SUM:
            return "(%s)" % result
        else:
            return result

    def map_list(self, expr, enclosing_prec):
        return "[%s]" % ", ".join([self.rec(i, PREC_NONE) for i in expr.children])

