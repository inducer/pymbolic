import pymbolic.primitives as primitives




try:
    import numpy

    def is_numpy_array(val):
        return isinstance(val, numpy.ndarray)
except ImportError:
    def is_numpy_array(ary):
        return False




class UnsupportedExpressionError(ValueError):
    pass



class Mapper(object):
    def handle_unsupported_expression(self, expr, *args):
        raise UnsupportedExpressionError(
                "%s cannot handle expressions of type %s" % (
                    self.__class__, expr.__class__))

    def __call__(self, expr, *args):
        try:
            method = expr.get_mapper_method(self)
        except AttributeError:
            if isinstance(expr, primitives.Expression):
                return self.handle_unsupported_expression(expr, *args)
            else:
                return self.map_foreign(expr, *args)
        else:
            return method(expr, *args)

    def map_variable(self, expr, *args):
        return self.map_algebraic_leaf(expr, *args)

    def map_subscript(self, expr, *args):
        return self.map_algebraic_leaf(expr, *args)

    def map_call(self, expr, *args):
        return self.map_algebraic_leaf(expr, *args)

    def map_lookup(self, expr, *args):
        return self.map_algebraic_leaf(expr, *args)

    def map_if_positive(self, expr, *args):
        return self.map_algebraic_leaf(expr, *args)

    def map_rational(self, expr, *args):
        return self.map_quotient(expr, *args)

    def map_foreign(self, expr, *args):
        if isinstance(expr, primitives.VALID_CONSTANT_CLASSES):
            return self.map_constant(expr, *args)
        elif isinstance(expr, list):
            return self.map_list(expr, *args)
        elif is_numpy_array(expr):
            return self.map_numpy_array(expr, *args)
        else:
            raise ValueError, "%s encountered invalid foreign object: %s" % (
                    self.__class__, repr(expr))





class RecursiveMapper(Mapper):
    def rec(self, expr, *args):
        try:
            method = expr.get_mapper_method(self)
        except AttributeError:
            if isinstance(expr, primitives.Expression):
                return self.handle_unsupported_expression(expr, *args)
            else:
                return self.map_foreign(expr, *args)
        else:
            return method(expr, *args)




class CombineMapper(RecursiveMapper):
    def map_call(self, expr, *args):
        return self.combine(
                (self.rec(expr.function, *args),) +
                tuple(
                    self.rec(child, *args) for child in expr.parameters)
                )

    def map_subscript(self, expr, *args):
        return self.combine(
                [self.rec(expr.aggregate, *args),
                    self.rec(expr.index, *args)])

    def map_lookup(self, expr, *args):
        return self.rec(expr.aggregate, *args)

    def map_negation(self, expr, *args):
        return self.rec(expr.child, *args)

    def map_sum(self, expr, *args):
        return self.combine(self.rec(child, *args)
                for child in expr.children)

    map_product = map_sum

    def map_quotient(self, expr, *args):
        return self.combine((
            self.rec(expr.numerator, *args),
            self.rec(expr.denominator, *args)))

    def map_power(self, expr, *args):
        return self.combine((
                self.rec(expr.base, *args),
                self.rec(expr.exponent, *args)))

    def map_polynomial(self, expr, *args):
        return self.combine(
                (self.rec(expr.base, *args),) +
                tuple(
                    self.rec(coeff, *args) for exp, coeff in expr.data)
                )

    map_list = map_sum
    map_vector = map_sum

    def map_numpy_array(self, expr, *args):
        return self.combine(self.rec(el) for el in expr.flat)

    def map_common_subexpression(self, expr, *args):
        return self.rec(expr.child, *args)

    def map_if_positive(self, expr):
        return self.combine([
            self.rec(expr.criterion),
            self.rec(expr.then),
            self.rec(expr.else_)])




class IdentityMapperBase(object):
    def map_constant(self, expr, *args):
        # leaf -- no need to rebuild
        return expr

    def map_variable(self, expr, *args):
        # leaf -- no need to rebuild
        return expr

    def map_function_symbol(self, expr, *args):
        return expr

    def map_call(self, expr, *args):
        return expr.__class__(
                self.rec(expr.function, *args),
                tuple(self.rec(child, *args)
                    for child in expr.parameters))

    def map_subscript(self, expr, *args):
        return expr.__class__(
                self.rec(expr.aggregate, *args),
                self.rec(expr.index, *args))

    def map_lookup(self, expr, *args):
        return expr.__class__(
                self.rec(expr.aggregate, *args),
                expr.name)

    def map_negation(self, expr, *args):
        return expr.__class__(self.rec(expr.child, *args))

    def map_sum(self, expr, *args):
        from pymbolic.primitives import flattened_sum
        return flattened_sum(tuple(
            self.rec(child, *args) for child in expr.children))

    def map_product(self, expr, *args):
        from pymbolic.primitives import flattened_product
        return flattened_product(tuple(
            self.rec(child, *args) for child in expr.children))

    def map_quotient(self, expr, *args):
        return expr.__class__(self.rec(expr.numerator, *args),
                              self.rec(expr.denominator, *args))

    def map_power(self, expr, *args):
        return expr.__class__(self.rec(expr.base, *args),
                              self.rec(expr.exponent, *args))

    def map_polynomial(self, expr, *args):
        return expr.__class__(self.rec(expr.base, *args),
                              ((exp, self.rec(coeff, *args))
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

    def map_common_subexpression(self, expr, *args, **kwargs):
        from pymbolic.primitives import is_zero
        result = self.rec(expr.child, *args, **kwargs)
        if is_zero(result):
            return 0

        return expr.__class__(
                result,
                expr.prefix,
                **expr.get_extra_properties())

    def map_if_positive(self, expr):
        return expr.__class__(
                self.rec(expr.criterion),
                self.rec(expr.then),
                self.rec(expr.else_),
                )




class IdentityMapper(IdentityMapperBase, RecursiveMapper):
    pass

class NonrecursiveIdentityMapper(IdentityMapperBase, Mapper):
    pass




class CSECachingMapperMixin(object):
    def map_common_subexpression(self, expr):
        from pymbolic.primitives import is_zero

        try:
            ccd = self._cse_cache_dict
        except AttributeError:
            from weakref import WeakKeyDictionary
            ccd = self._cse_cache_dict = WeakKeyDictionary()

        try:
            return ccd[expr]
        except KeyError:
            result = self.map_common_subexpression_uncached(expr)
            ccd[expr] = result
            return result
