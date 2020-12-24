import pymbolic


class EqualizerMapper(pymbolic.mapper.Mapper):
    """A mapper for recursively checking the equality of two expression trees."""

    def map_constant(self, expr, other, *args, **kwargs):
        return expr == other

    def map_variable(self, expr, other, *args, **kwargs):
        return expr.name == other.name

    def map_function_symbol(self, expr, other, *args, **kwargs):
        return expr.__class__.__name__ == other.__class__.__name__

    def map_call(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.function, other.function, *args, **kwargs) \
                and self.rec(expr.parameters, other.parameters, *args, **kwargs)

    def map_call_with_kwargs(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.function, other.function, *args, **kwargs) \
                and self.rec(expr.parameters, other.parameters, *args, **kwargs) \
                and self.rec(tuple(expr.kw_parameters.keys()),
                             tuple(other.kw_parameters.keys()), *args, **kwargs) \
                and self.rec(tuple(expr.kw_parameters.values()),
                             tuple(other.kw_parameters.values()), *args, **kwargs)

    def map_subscript(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.aggregate, other.aggregate, *args, **kwargs) \
                and self.rec(expr.index, other.index, *args, **kwargs)

    def map_lookup(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.aggregate, other.aggregate, *args, **kwargs) \
                and self.rec(expr.name, other.name, *args, **kwargs)

    def _map_multichild_expr(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.children, other.children, *args, **kwargs)

    def map_sum(self, expr, other, *args, **kwargs):
        return self._map_multichild_expr(expr, other, *args, **kwargs)

    def map_product(self, expr, other, *args, **kwargs):
        return self._map_multichild_expr(expr, other, *args, **kwargs)

    def _map_quotient_base(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.numerator, other.numerator, *args, **kwargs)

    def map_quotient(self, expr, other, *args, **kwargs):
        return self._map_quotient_base(expr, other, *args, **kwargs)

    def map_floor_div(self, expr, other, *args, **kwargs):
        return self._map_quotient_base(expr, other, *args, **kwargs)

    def map_remainder(self, expr, other, *args, **kwargs):
        return self._map_quotient_base(expr, other, *args, **kwargs)

    def map_power(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.base, other.base, *args, **kwargs) \
                and self.rec(expr.exponent, other.exponent, *args, **kwargs)

    def map_polynomial(self, expr, other, *args, **kwargs):
        from pymbolic.primitives import flattened_sum
        return type(expr) == type(other) \
                and self.rec(flattened_sum([coeff * expr.base**exp for exp, coeff in expr.data[::-1]]),
                             flattened_sum([coeff * expr.base**exp for exp, coeff in other.data[::-1]]),
                             *args, **kwargs)

    def _map_shift_operator(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.shiftee, other.shiftee, *args, **kwargs) \
                and self.rec(expr.shift, other.shift, *args, **kwargs)

    def map_left_shift(self, expr, other, *args, **kwargs):
        return self._map_shift_operator(expr, other, *args, **kwargs)

    def map_right_shift(self, expr, other, *args, **kwargs):
        return self._map_shift_operator(expr, other, *args, **kwargs)

    def map_bitwise_not(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.child, other.child, *args, **kwargs)

    def map_bitwise_or(self, expr, other, *args, **kwargs):
        return self._map_multichild_expr(expr, other, *args, **kwargs)

    def map_bitwise_xor(self, expr, other, *args, **kwargs):
        return self._map_multichild_expr(expr, other, *args, **kwargs)

    def map_bitwise_and(self, expr, other, *args, **kwargs):
        return self._map_multichild_expr(expr, other, *args, **kwargs)

    def map_comparison(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and expr.operator == other.operator \
                and self.rec(expr.left, other.left, *args, **kwargs) \
                and self.rec(expr.right, other.right, *args, **kwargs)

    def map_logical_not(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.child, other.child, *args, **kwargs)

    def map_logical_or(self, expr, other, *args, **kwargs):
        return self._map_multichild_expr(expr, other, *args, **kwargs)

    def map_logical_and(self, expr, other, *args, **kwargs):
        return self._map_multichild_expr(expr, other, *args, **kwargs)

    def map_list(self, expr, other, *args, **kwargs):
        return expr == other

    def map_tuple(self, expr, other, *args, **kwargs):
        return expr == other

    def map_numpy_array(self, expr, other, *args, **kwargs):
        import numpy
        return numpy.array_equal(expr, other)

    def map_multivector(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.data == other.data \
                and self.space == other.space

    def map_common_subexpression(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.child, other.child, *args, **kwargs) \
                and self.rec(expr.prefix, other.prefix, *args, **kwargs) \
                and self.rec(expr.scope, other.scope, *args, **kwargs)

    def map_if(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.condition, other.condition, *args, **kwargs) \
                and self.rec(expr.then, other.then, *args, **kwargs) \
                and self.rec(expr.else_, other.else_, *args, **kwargs)

    def map_if_positive(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.criterion, other.criterion, *args, **kwargs) \
                and self.rec(expr.then, other.then, *args, **kwargs) \
                and self.rec(expr.else_, other.else_, *args, **kwargs)

    def map_min(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.children, other.children, *args, **kwargs)

    map_max = map_min

    def map_derivative(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
                and self.rec(expr.child, other.child, *args, **kwargs) \
                and self.rec(expr.varaibles, other.variables, *args, **kwargs)

    def map_substitution(self, expr, other, *args, **kwargs):
        return type(expr) == type(other) \
               and self.rec(expr.child, other.child, *args, **kwargs) \
               and self.rec(expr.variables, other.variables, *args, **kwargs) \
               and self.rec(expr.values, other.values, *args, **kwargs)

    def map_slice(self, expr, other, *args, **kwargs):
        return self._map_multichild_expr(expr, other, *args, **kwargs)

    def __call__(self, expr, other, *args, **kwargs):
        return super(EqualizerMapper, self).__call__(expr, other, *args, **kwargs)
