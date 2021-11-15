__copyright__ = "Copyright (C) 2021 Alexandru Fikl"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from typing import Any, Dict, Tuple

from pymbolic.mapper import Mapper, UnsupportedExpressionError
from pymbolic.primitives import Expression


class EqualityMapper(Mapper):
    __slots__ = ["_ids_to_result"]

    def __init__(self) -> None:
        self._ids_to_result: Dict[Tuple[int, int], bool] = {}

    def rec(self, expr: Any, other: Any) -> bool:
        key = (id(expr), id(other))
        if key in self._ids_to_result:
            return self._ids_to_result[key]

        if expr is other:
            result = True
        elif expr.__class__ != other.__class__:
            result = False
        else:
            try:
                method = getattr(self, expr.mapper_method)
            except AttributeError:
                if isinstance(expr, Expression):
                    result = self.handle_unsupported_expression(expr, other)
                else:
                    result = self.map_foreign(expr, other)
            else:
                result = method(expr, other)

        self._ids_to_result[key] = result
        return result

    def __call__(self, expr: Any, other: Any) -> bool:
        return self.rec(expr, other)

    # {{{ handle_unsupported_expression

    def handle_unsupported_expression(self, expr, other) -> bool:
        eq = expr.make_equality_mapper()
        if type(self) == type(eq):
            raise UnsupportedExpressionError(
                    "'{}' cannot handle expressions of type '{}'".format(
                        type(self).__name__, type(expr).__name__))

        # NOTE: this may look fishy, but we want to preserve the cache as we
        # go through the expression tree, so that it does not do
        # unnecessary checks when we change the mapper for some subclass
        eq._ids_to_result = self._ids_to_result

        return eq(expr, other)

    # }}}

    # {{{ foreign

    def map_tuple(self, expr, other) -> bool:
        return (
                len(expr) == len(other)
                and all(self.rec(el, other_el)
                    for el, other_el in zip(expr, other)))

    def map_foreign(self, expr, other) -> bool:
        import numpy as np
        from pymbolic.primitives import VALID_CONSTANT_CLASSES

        if isinstance(expr, VALID_CONSTANT_CLASSES):
            return expr == other
        elif isinstance(expr, (np.ndarray, tuple)):
            return self.map_tuple(expr, other)
        else:
            raise ValueError(
                    f"{type(self).__name__} encountered invalid foreign object: "
                    f"{expr!r}")

    # }}}

    # {{{ primitives

    # NOTE: `type(expr) == type(other)` is checked in `__call__`, so the
    # checks below can assume that the two operands always have the same type

    # NOTE: as much as possible, these should try to put the "cheap" checks
    # first so that the shortcircuiting removes the need to to extra work

    # NOTE: `all` is also shortcircuiting, so should be better to use a
    # generator there to avoid extra work

    def map_nan(self, expr, other) -> bool:
        return True

    def map_wildcard(self, expr, other) -> bool:
        return True

    def map_function_symbol(self, expr, other) -> bool:
        return True

    def map_variable(self, expr, other) -> bool:
        return expr.name == other.name

    def map_subscript(self, expr, other) -> bool:
        return (
                self.rec(expr.index, other.index)
                and self.rec(expr.aggregate, other.aggregate))

    def map_lookup(self, expr, other) -> bool:
        return (
                expr.name == other.name
                and self.rec(expr.aggregate, other.aggregate))

    def map_call(self, expr, other) -> bool:
        return (
                len(expr.parameters) == len(other.parameters)
                and self.rec(expr.function, other.function)
                and all(self.rec(p, other_p)
                    for p, other_p in zip(expr.parameters, other.parameters)))

    def map_call_with_kwargs(self, expr, other) -> bool:
        return (
                len(expr.parameters) == len(other.parameters)
                and len(expr.kw_parameters) == len(other.kw_parameters)
                and self.rec(expr.function, other.function)
                and all(self.rec(p, other_p)
                    for p, other_p in zip(expr.parameters, other.parameters))
                and all(k == other_k and self.rec(v, other_v)
                    for (k, v), (other_k, other_v) in zip(
                        sorted(expr.kw_parameters.items()),
                        sorted(other.kw_parameters.items()))))

    def map_sum(self, expr, other) -> bool:
        return (
                len(expr.children) == len(other.children)
                and all(self.rec(child, other_child)
                    for child, other_child in zip(expr.children, other.children))
                )

    map_slice = map_sum
    map_product = map_sum
    map_min = map_sum
    map_max = map_sum

    def map_bitwise_not(self, expr, other) -> bool:
        return self.rec(expr.child, other.child)

    map_bitwise_and = map_sum
    map_bitwise_or = map_sum
    map_bitwise_xor = map_sum
    map_logical_and = map_sum
    map_logical_or = map_sum
    map_logical_not = map_bitwise_not

    def map_quotient(self, expr, other) -> bool:
        return (
                self.rec(expr.numerator, other.numerator)
                and self.rec(expr.denominator, other.denominator)
                )

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, other) -> bool:
        return (
                self.rec(expr.base, other.base)
                and self.rec(expr.exponent, other.exponent)
                )

    def map_left_shift(self, expr, other) -> bool:
        return (
                self.rec(expr.shift, other.shift)
                and self.rec(expr.shiftee, other.shiftee))

    map_right_shift = map_left_shift

    def map_comparison(self, expr, other) -> bool:
        return (
                expr.operator == other.operator
                and self.rec(expr.left, other.left)
                and self.rec(expr.right, other.right))

    def map_if(self, expr, other) -> bool:
        return (
                self.rec(expr.condition, other.condition)
                and self.rec(expr.then, other.then)
                and self.rec(expr.else_, other.else_))

    def map_if_positive(self, expr, other) -> bool:
        return (
                self.rec(expr.criterion, other.criterion)
                and self.rec(expr.then, other.then)
                and self.rec(expr.else_, other.else_))

    def map_common_subexpression(self, expr, other) -> bool:
        return (
                expr.prefix == other.prefix
                and expr.scope == other.scope
                and self.rec(expr.child, other.child)
                and all(k == other_k and v == other_v
                    for (k, v), (other_k, other_v) in zip(
                        expr.get_extra_properties(),
                        other.get_extra_properties())))

    def map_substitution(self, expr, other) -> bool:
        return (
                len(expr.variables) == len(other.variables)
                and len(expr.values) == len(other.values)
                and expr.variables == other.variables
                and self.rec(expr.child, other.child)
                and all(self.rec(v, other_v)
                    for v, other_v in zip(expr.values, other.values))
                )

    def map_derivative(self, expr, other) -> bool:
        return (
                len(expr.variables) == len(other.variables)
                and self.rec(expr.child, other.child)
                and all(self.rec(v, other_v)
                    for v, other_v in zip(expr.variables, other.variables)))

    def map_polynomial(self, expr, other) -> bool:
        return (
                self.rec(expr.Base, other.Data)
                and self.rec(expr.Data, other.Data))

    # }}}

    # {{{ geometry_algebra.primitives

    def map_nabla_component(self, expr, other) -> bool:
        return (
                expr.ambient_axis == other.ambient_axis
                and expr.nabla_id == other.nabla_id
                )

    # }}}
