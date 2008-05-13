import pymbolic.mapper




PREC_CALL = 5
PREC_POWER = 4
PREC_UNARY = 3
PREC_PRODUCT = 2
PREC_SUM = 1
PREC_NONE = 0



class StringifyMapper(pymbolic.mapper.RecursiveMapper):
    def __init__(self, constant_mapper=str):
        self.constant_mapper = constant_mapper

    def handle_unsupported_expression(self, victim, enclosing_prec):
        strifier = victim.stringifier()
        if isinstance(self, strifier):
            raise ValueError("stringifier '%s' can't handle '%s'" 
                    % (self, victim.__class__))
        return strifier(self.constant_mapper)(victim, enclosing_prec)

    def map_constant(self, expr, enclosing_prec):
        result = self.constant_mapper(expr)

        if (
                (isinstance(expr, (int, float, long)) and expr < 0) 
                or 
                (isinstance(expr, complex) and expr.imag and expr.real)
                ) and (enclosing_prec > PREC_SUM):
            return "(%s)" % result
        else:
            return result


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

    def map_sum(self, expr, enclosing_prec):
        result = " + ".join(self.rec(i, PREC_SUM) for i in expr.children)
        if enclosing_prec > PREC_SUM:
            return "(%s)" % result
        else:
            return result

    def map_product(self, expr, enclosing_prec):
        result = "*".join(self.rec(i, PREC_PRODUCT) for i in expr.children)
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
        sbase = self(expr.base, PREC_POWER)
        def stringify_expcoeff((exp, coeff)):
            if exp == 0:
                return self(coeff, PREC_SUM)
            elif exp == 1:
                strexp = ""
            else:
                strexp = "**%s" % exp

            if not (coeff-1):
                return "%s%s" % (sbase, strexp) 
            elif not (coeff+1):
                return "-%s%s" % (sbase, strexp) 
            else:
                return "%s*%s%s" % (self(coeff, PREC_PRODUCT), sbase, strexp) 

        if not expr.data:
            return "0"

        result = "%s" % " + ".join(stringify_expcoeff(i) for i in expr.data[::-1])
        if enclosing_prec > PREC_SUM and len(expr.data) > 1:
            return "(%s)" % result
        else:
            return result

    def map_list(self, expr, enclosing_prec):
        return "[%s]" % ", ".join([self.rec(i, PREC_NONE) for i in expr])

    map_vector = map_list

    def map_numpy_array(self, expr, enclosing_prec):
        return 'array(%s)' % str(expr)
