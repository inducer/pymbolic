try:
    import numpy

    def is_numpy_array(val):
        return isinstance(val, numpy.ndarray)
except ImportError:
    def is_numpy_array(ary):
        return False




class Mapper(object):
    def __init__(self, recurse=True):
        self.Recurse = True

    def handle_unsupported_expression(self, expr, *args, **kwargs):
        raise ValueError, "%s cannot handle expressions of type %s" % (
                self.__class__, expr.__class__)

    def __call__(self, expr, *args, **kwargs):
        import pymbolic.primitives as primitives
        if isinstance(expr, primitives.Expression):
            try:
                method = expr.get_mapper_method(self)
            except AttributeError:
                return self.handle_unsupported_expression(expr, *args, **kwargs)
            else:
                return method(expr, *args, **kwargs)
        else:
            return self.map_foreign(expr, *args, **kwargs)

    def map_variable(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_subscript(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_call(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_lookup(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_rational(self, expr, *args, **kwargs):
        return self.map_quotient(expr, *args, **kwargs)

    def map_foreign(self, expr, *args, **kwargs):
        from pymbolic.primitives import is_constant
        
        if is_constant(expr):
            return self.map_constant(expr, *args, **kwargs)
        elif isinstance(expr, list):
            return self.map_list(expr, *args, **kwargs)
        elif is_numpy_array(expr):
            return self.map_numpy_array(expr, *args, **kwargs)
        else:
            raise ValueError, "%s encountered invalid foreign object: %s" % (
                    self.__class__, repr(expr))





class RecursiveMapper(Mapper):
    def rec(self, expr, *args, **kwargs):
        import pymbolic.primitives as primitives
        if isinstance(expr, primitives.Expression):
            try:
                method = expr.get_mapper_method(self)
            except AttributeError:
                return self.handle_unsupported_expression(expr, *args, **kwargs)
            else:
                return method(expr, *args, **kwargs)
        else:
            return self.map_foreign(expr, *args, **kwargs)




class CombineMapper(RecursiveMapper):
    def map_call(self, expr, *args, **kwargs):
        return self.combine(
                (self.rec(expr.function, *args, **kwargs),) + 
                tuple(
                    self.rec(child, *args, **kwargs) for child in expr.parameters)
                )

    def map_subscript(self, expr, *args, **kwargs):
        return self.combine(
                [self.rec(expr.aggregate, *args, **kwargs), 
                    self.rec(expr.index, *args, **kwargs)])

    def map_lookup(self, expr, *args, **kwargs):
        return self.rec(expr.aggregate, *args, **kwargs)

    def map_negation(self, expr, *args, **kwargs):
        return self.rec(expr.child, *args, **kwargs)

    def map_sum(self, expr, *args, **kwargs):
        return self.combine(self.rec(child, *args, **kwargs) 
                for child in expr.children)

    map_product = map_sum

    def map_quotient(self, expr, *args, **kwargs):
        return self.combine((
            self.rec(expr.numerator, *args, **kwargs), 
            self.rec(expr.denominator, *args, **kwargs)))

    def map_power(self, expr, *args, **kwargs):
        return self.combine((
                self.rec(expr.base, *args, **kwargs), 
                self.rec(expr.exponent, *args, **kwargs)))

    def map_polynomial(self, expr, *args, **kwargs):
        return self.combine(
                (self.rec(expr.base, *args, **kwargs),) + 
                tuple(
                    self.rec(coeff, *args, **kwargs) for exp, coeff in expr.data)
                )

    map_list = map_sum
    map_vector = map_sum

    def map_numpy_array(self, expr):
        return self.combine(expr.flat)



class IdentityMapperBase(object):
    def map_constant(self, expr, *args, **kwargs):
        # leaf -- no need to rebuild
        return expr

    def map_variable(self, expr, *args, **kwargs):
        # leaf -- no need to rebuild
        return expr

    def map_call(self, expr, *args, **kwargs):
        return expr.__class__(
                self.rec(expr.function, *args, **kwargs),
                tuple(self.rec(child, *args, **kwargs)
                    for child in expr.parameters))

    def map_subscript(self, expr, *args, **kwargs):
        return expr.__class__(
                self.rec(expr.aggregate, *args, **kwargs), 
                self.rec(expr.index, *args, **kwargs))

    def map_lookup(self, expr, *args, **kwargs):
        return expr.__class__(
                self.rec(expr.aggregate, *args, **kwargs), 
                expr.name)

    def map_negation(self, expr, *args, **kwargs):
        return expr.__class__(self.rec(expr.child, *args, **kwargs))

    def map_sum(self, expr, *args, **kwargs):
        from pymbolic.primitives import flattened_sum
        return flattened_sum(tuple(
            self.rec(child, *args, **kwargs) for child in expr.children))
    
    def map_product(self, expr, *args, **kwargs):
        from pymbolic.primitives import flattened_product
        return flattened_product(tuple(
            self.rec(child, *args, **kwargs) for child in expr.children))
    
    def map_quotient(self, expr, *args, **kwargs):
        return expr.__class__(self.rec(expr.numerator, *args, **kwargs),
                              self.rec(expr.denominator, *args, **kwargs))

    def map_power(self, expr, *args, **kwargs):
        return expr.__class__(self.rec(expr.base, *args, **kwargs),
                              self.rec(expr.exponent, *args, **kwargs))

    def map_polynomial(self, expr, *args, **kwargs):
        return expr.__class__(self.rec(expr.base, *args, **kwargs),
                              ((exp, self.rec(coeff, *args, **kwargs))
                                  for exp, coeff in expr.data))

    map_list = map_sum
    map_vector = map_sum

    def map_numpy_array(self, expr):
        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        from pytools import indices_in_shape
        for i in indices_in_shape(expr.shape):
            result[i] = self.rec(expr[i])
        return result



class IdentityMapper(IdentityMapperBase, RecursiveMapper):
    pass

class NonrecursiveIdentityMapper(IdentityMapperBase, Mapper):
    pass
