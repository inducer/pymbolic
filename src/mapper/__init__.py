class CombineMapper:
    def combine(self, values):
        raise NotImplementedError

    def map_call(self, expr):
        return self.combine([expr.function.invoke_mapper(self)] + 
                            [child.invoke_mapper(self)
                             for child in expr.parameters])

    def map_subscript(self, expr):
        return self.combine([expr.aggregate.invoke_mapper(self),
                             expr.index.invoke_mapper(self)])

    def map_lookup(self, expr):
        return expr.aggregate.invoke_mapper(self)

    def map_negation(self, expr):
        return expr.child.invoke_mapper(self)

    def map_sum(self, expr):
        return self.combine(child.invoke_mapper(self)
                            for child in expr.children)

    map_product = map_sum

    def map_rational(self, expr):
        return self.combine((expr.numerator.invoke_mapper(self),
                             expr.denominator.invoke_mapper(self)))

    def map_power(self, expr):
        return self.combine((expr.base.invoke_mapper(self),
                             expr.exponent.invoke_mapper(self)))

    def map_polynomial(self, expr):
        raise NotImplementedError
    
    map_list = map_sum





class IdentityMapper:
    def map_constant(self, expr):
        return expr

    def map_variable(self, expr):
        return expr

    def map_call(self, expr):
        return expr.__class__(expr.function.invoke_mapper(self),
                              tuple(child.invoke_mapper(self)
                                    for child in expr.parameters))

    def map_subscript(self, expr):
        return expr.__class__(expr.aggregate.invoke_mapper(self),
                              expr.index.invoke_mapper(self))

    def map_lookup(self, expr):
        return expr.__class__(expr.aggregate.invoke_mapper(self),
                              expr.name)

    def map_negation(self, expr):
        return expr.__class__(expr.child.invoke_mapper(self))

    def map_sum(self, expr):
        return expr.__class__(*[child.invoke_mapper(self)
                                for child in expr.children])
    
    map_product = map_sum
    
    def map_rational(self, expr):
        return expr.__class__(expr.numerator.invoke_mapper(self),
                              expr.denominator.invoke_mapper(self))

    def map_power(self, expr):
        return expr.__class__(expr.base.invoke_mapper(self),
                              expr.exponent.invoke_mapper(self))

    def map_polynomial(self, expr):
        raise NotImplementedError

    map_list = map_sum

