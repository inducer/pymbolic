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


# {{{ mapper base

class Mapper(object):
    def handle_unsupported_expression(self, expr, *args):
        raise UnsupportedExpressionError(
                "%s cannot handle expressions of type %s" % (
                    self.__class__, expr.__class__))

    def __call__(self, expr, *args, **kwargs):
        try:
            method = getattr(self, expr.mapper_method)
        except AttributeError:
            try:
                method = expr.get_mapper_method(self)
            except AttributeError:
                if isinstance(expr, primitives.Expression):
                    return self.handle_unsupported_expression(expr, *args, **kwargs)
                else:
                    return self.map_foreign(expr, *args, **kwargs)

        return method(expr, *args, **kwargs)

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
        elif isinstance(expr, tuple):
            return self.map_tuple(expr, *args)
        elif is_numpy_array(expr):
            return self.map_numpy_array(expr, *args)
        else:
            raise ValueError, "%s encountered invalid foreign object: %s" % (
                    self.__class__, repr(expr))

# }}}





class RecursiveMapper(Mapper):
    rec = Mapper.__call__



# {{{ combine mapper

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

    map_floor_div = map_quotient
    map_remainder = map_quotient

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

    def map_logical_and(self, expr, *args):
        return self.combine(self.rec(child, *args)
                for child in expr.children)

    map_logical_or = map_logical_and
    map_logical_not = map_negation

    def map_comparison(self, expr, *args):
        return self.combine((
            self.rec(expr.left, *args),
            self.rec(expr.right, *args)))

    def map_list(self, expr, *args):
        return self.combine(self.rec(child, *args) for child in expr)

    map_tuple = map_list

    def map_numpy_array(self, expr, *args):
        return self.combine(self.rec(el) for el in expr.flat)

    def map_common_subexpression(self, expr, *args):
        return self.rec(expr.child, *args)

    def map_if_positive(self, expr):
        return self.combine([
            self.rec(expr.criterion),
            self.rec(expr.then),
            self.rec(expr.else_)])

    def map_if(self, expr):
        return self.combine([
            self.rec(expr.condition),
            self.rec(expr.then),
            self.rec(expr.else_)])

# }}}

# {{{ identity mapper

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

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, *args):
        return expr.__class__(self.rec(expr.base, *args),
                              self.rec(expr.exponent, *args))

    def map_polynomial(self, expr, *args):
        return expr.__class__(self.rec(expr.base, *args),
                              ((exp, self.rec(coeff, *args))
                                  for exp, coeff in expr.data))

    def map_logical_and(self, expr, *args):
        return type(expr)(tuple(
            self.rec(child, *args) for child in expr.children))

    map_logical_or = map_logical_and

    def map_logical_not(self, expr, *args):
        from pymbolic.primitives import LogicalNot
        return LogicalNot(
                self.rec(expr.child, *args))

    def map_comparison(self, expr, *args):
        return type(expr)(
                self.rec(expr.left, *args),
                expr.operator,
                self.rec(expr.right, *args))

    def map_list(self, expr, *args):
        return [self.rec(child, *args) for child in expr]

    def map_tuple(self, expr, *args):
        return tuple(self.rec(child, *args) for child in expr)

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

        return type(expr)(
                result,
                expr.prefix,
                **expr.get_extra_properties())

    def map_substitution(self, expr, *args):
        return type(expr)(
                self.rec(expr.child, *args),
                expr.variables,
                tuple(self.rec(v, *args) for v in expr.values))

    def map_derivative(self, expr, *args):
        return type(expr)(
                self.rec(expr.child, *args),
                expr.variables)

    def map_slice(self, expr, *args):
        def do_map(expr):
            if expr is None:
                return expr
            else:
                return self.rec(ch, *args)

        return type(expr)(
                tuple(do_map(ch) for ch in expr.children))

    def map_if_positive(self, expr, *args):
        return type(expr)(
                self.rec(expr.criterion, *args),
                self.rec(expr.then, *args),
                self.rec(expr.else_, *args))

    def map_if(self, expr, *args):
        return type(expr)(
                self.rec(expr.condition, *args),
                self.rec(expr.then, *args),
                self.rec(expr.else_, *args))



class IdentityMapper(IdentityMapperBase, RecursiveMapper):
    pass

class NonrecursiveIdentityMapper(IdentityMapperBase, Mapper):
    pass

# }}}

# {{{ walk mapper

class WalkMapper(RecursiveMapper):
    def map_constant(self, expr, *args):
        self.visit(expr)

    def map_variable(self, expr, *args):
        self.visit(expr)

    def map_function_symbol(self, expr, *args):
        self.visit(expr)

    def map_call(self, expr, *args):
        if not self.visit(expr):
            return

        self.rec(expr.function, *args)
        for child in expr.parameters:
            self.rec(child, *args)

    def map_subscript(self, expr, *args):
        if not self.visit(expr):
            return

        self.rec(expr.aggregate, *args)
        self.rec(expr.index, *args)

    def map_lookup(self, expr, *args):
        if not self.visit(expr):
            return

        self.rec(expr.aggregate, *args)

    def map_negation(self, expr, *args):
        if not self.visit(expr):
            return

        self.rec(expr.child, *args)

    def map_sum(self, expr, *args):
        if not self.visit(expr):
            return

        for child in expr.children:
            self.rec(child, *args)

    map_product = map_sum

    def map_quotient(self, expr, *args):
        if not self.visit(expr):
            return

        self.rec(expr.numerator, *args)
        self.rec(expr.denominator, *args)

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, *args):
        if not self.visit(expr):
            return

        self.rec(expr.base, *args)
        self.rec(expr.exponent, *args)

    def map_polynomial(self, expr, *args):
        if not self.visit(expr):
            return

        self.rec(expr.base, *args)
        for exp, coeff in expr.data:
            self.rec(coeff, *args)

    def map_list(self, expr, *args):
        if not self.visit(expr):
            return

        for child in expr:
            self.rec(child, *args)

    map_tuple = map_list

    def map_numpy_array(self, expr):
        if not self.visit(expr):
            return

        from pytools import indices_in_shape
        for i in indices_in_shape(expr.shape):
            self.rec(expr[i])

    def map_common_subexpression(self, expr, *args, **kwargs):
        if not self.visit(expr):
            return

        self.rec(expr.child)

    def map_comparison(self, expr):
        if not self.visit(expr):
            return

        self.rec(expr.left)
        self.rec(expr.right)

    def map_logical_not(self, expr):
        if not self.visit(expr):
            return

        self.rec(expr.child)

    map_logical_and = map_sum
    map_logical_or = map_sum

    def map_if(self, expr):
        if not self.visit(expr):
            return

        self.rec(expr.condition)
        self.rec(expr.then)
        self.rec(expr.else_)

    def map_if_positive(self, expr):
        if not self.visit(expr):
            return

        self.rec(expr.criterion)
        self.rec(expr.then)
        self.rec(expr.else_)

    def map_substitution(self, expr):
        if not self.visit(expr):
            return

        self.rec(expr.child)
        for v in expr.values:
            self.rec(v)

    def map_derivative(self, expr):
        if not self.visit(expr):
            return

        self.rec(expr.child)

    def visit(self, expr):
        return True

# }}}

# {{{ callback mapper

class CallbackMapper(RecursiveMapper):
    def __init__(self, function, fallback_mapper):
        self.function = function
        self.fallback_mapper = fallback_mapper
        fallback_mapper.rec = self.rec

    def map_constant(self, expr, *args):
        return self.function(expr, self, *args)

    map_variable = map_constant
    map_function_symbol = map_constant
    map_call = map_constant
    map_subscript = map_constant
    map_lookup = map_constant
    map_negation = map_constant
    map_sum = map_constant
    map_product = map_constant
    map_quotient = map_constant
    map_floor_div = map_constant
    map_remainder = map_constant
    map_power = map_constant
    map_polynomial = map_constant
    map_list = map_constant
    map_tuple = map_constant
    map_numpy_array = map_constant
    map_common_subexpression = map_constant
    map_if_positive = map_constant

# }}}

# {{{ cse caching mixin

class CSECachingMapperMixin(object):
    def map_common_subexpression(self, expr):
        try:
            ccd = self._cse_cache_dict
        except AttributeError:
            ccd = self._cse_cache_dict = {}

        try:
            return ccd[expr]
        except KeyError:
            result = self.map_common_subexpression_uncached(expr)
            ccd[expr] = result
            return result

# }}}

# vim: foldmethod=marker
