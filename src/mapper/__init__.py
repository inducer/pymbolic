class Mapper(object):
    def __call__(self, victim, *args, **kwargs):
        try:
            return victim.invoke_mapper(self, *args, **kwargs)
        except AttributeError:
            return self.map_constant(victim, *args, **kwargs)

    def map_rational(self, expr, *args, **kwargs):
        return self.map_quotient(expr, *args, **kwargs)





class CombineMapper(Mapper):
    def combine(self, values):
        raise NotImplementedError

    def map_call(self, expr, *args, **kwargs):
        return self.combine(
                (self(expr.function, *args, **kwargs),) + 
                tuple(
                    self(child, *args, **kwargs) for child in expr.parameters)
                )

    def map_subscript(self, expr, *args, **kwargs):
        return self.combine(
                [self(expr.aggregate, *args, **kwargs), 
                    self(expr.index, *args, **kwargs)])

    def map_lookup(self, expr, *args, **kwargs):
        return self(expr.aggregate, *args, **kwargs)

    def map_negation(self, expr, *args, **kwargs):
        return self(expr.child, *args, **kwargs)

    def map_sum(self, expr, *args, **kwargs):
        return self.combine(self(child, *args, **kwargs) 
                for child in expr.children)

    map_product = map_sum

    def map_quotient(self, expr, *args, **kwargs):
        return self.combine((
            self(expr.numerator, *args, **kwargs), 
            self(expr.denominator, *args, **kwargs)))

    def map_power(self, expr, *args, **kwargs):
        return self.combine((
                self(expr.base, *args, **kwargs), 
                self(expr.exponent, *args, **kwargs)))

    map_list = map_sum





class IdentityMapper(Mapper):
    def map_constant(self, expr, *args, **kwargs):
        # leaf -- no need to rebuild
        return expr

    def map_variable(self, expr, *args, **kwargs):
        # leaf -- no need to rebuild
        return expr

    def map_call(self, expr, *args, **kwargs):
        return expr.__class__(
                self(expr.function, *args, **kwargs),
                tuple(self(child, *args, **kwargs)
                    for child in expr.parameters))

    def map_subscript(self, expr, *args, **kwargs):
        return expr.__class__(
                self(expr.aggregate, *args, **kwargs), 
                self(expr.index, *args, **kwargs))

    def map_lookup(self, expr, *args, **kwargs):
        return expr.__class__(
                self(expr.aggregate, *args, **kwargs), 
                expr.name)

    def map_negation(self, expr, *args, **kwargs):
        return expr.__class__(self(expr.child, *args, **kwargs))

    def map_sum(self, expr, *args, **kwargs):
        return expr.__class__(
                *[self(child, *args, **kwargs) 
                    for child in expr.children])
    
    map_product = map_sum
    
    def map_rational(self, expr, *args, **kwargs):
        return expr.__class__(self(expr.numerator, *args, **kwargs),
                              self(expr.denominator, *args, **kwargs))

    def map_power(self, expr, *args, **kwargs):
        return expr.__class__(self(expr.base, *args, **kwargs),
                              self(expr.exponent, *args, **kwargs))

    def map_polynomial(self, expr, *args, **kwargs):
        raise NotImplementedError

    map_list = map_sum

