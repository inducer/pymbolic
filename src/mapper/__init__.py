class Mapper(object):
    def __call__(self, victim, *args, **kwargs):
        try:
            victim.invoke_mapper(self, *args, **kwargs)
        except AttributeError:
            self.map_constant(victim)

    def map_rational(self, expr):
        return self.map_quotient(self, expr)





class CombineMapper(Mapper):
    def combine(self, values):
        raise NotImplementedError

    def map_call(self, expr):
        return self.combine([self(expr.function)] + 
                            [self(child) for child in expr.parameters])

    def map_subscript(self, expr):
        return self.combine(
                [self(expr.aggregate), self(expr.index)])

    def map_lookup(self, expr):
        return self(expr.aggregate)

    def map_negation(self, expr):
        return self(expr.child)

    def map_sum(self, expr):
        return self.combine(self(child) for child in expr.children)

    map_product = map_sum

    def map_quotient(self, expr):
        return self.combine((self(expr.numerator), self(expr.denominator)))

    def map_power(self, expr):
        return self.combine(self(expr.base), self(expr.exponent))

    map_list = map_sum





class IdentityMapper(Mapper):
    def map_constant(self, expr):
        return expr

    def map_variable(self, expr):
        return expr

    def map_call(self, expr):
        return expr.__class__(
                self(expr.function),
                tuple(self(child)
                    for child in expr.parameters))

    def map_subscript(self, expr):
        return expr.__class__(self(expr.aggregate), self(expr.index))

    def map_lookup(self, expr):
        return expr.__class__(self(expr.aggregate), expr.name)

    def map_negation(self, expr):
        return expr.__class__(self(expr.child))

    def map_sum(self, expr):
        return expr.__class__(
                *[self(child) for child in expr.children])
    
    map_product = map_sum
    
    def map_rational(self, expr):
        return expr.__class__(self(expr.numerator),
                              self(expr.denominator))

    def map_power(self, expr):
        return expr.__class__(self(expr.base),
                              self(expr.exponent))

    def map_polynomial(self, expr):
        raise NotImplementedError

    map_list = map_sum

