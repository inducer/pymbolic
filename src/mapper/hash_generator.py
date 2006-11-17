from pymbolic.mapper import Mapper




class HashMapper(Mapper):
    def map_constant(self, expr):
        return 0x131 ^ hash(expr.value)

    def map_variable(self, expr):
        return 0x111 ^ hash(expr.name)

    def map_call(self, expr):
        return hash(expr.function) ^ hash(expr.parameters)

    def map_subscript(self, expr):
        return 0x123 \
               ^ hash(expr.aggregate) \
               ^ hash(expr.index)

    def map_lookup(self, expr):
        return 0x183 \
               ^ hash(expr.aggregate) \
               ^ hash(expr.name)

    def map_negation(self, expr):
        return ~ hash(expr.child)

    def map_sum(self, expr):
        return 0x456 ^ hash(expr.children)

    def map_product(self, expr):
        return 0x789 ^ hash(expr.children)
    
    def map_rational(self, expr):
        return 0xabc \
               ^ hash(expr.numerator) \
               ^ hash(expr.denominator)

    def map_power(self, expr):
        return 0xdef \
               ^ hash(expr.base) \
               ^ hash(expr.exponent)

    def map_polynomial(self, expr):
        raise NotImplementedError

    def map_product(self, expr):
        return 0x124 ^ hash(expr.children)

