from __future__ import division

__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

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

import pymbolic.primitives as primitives

__doc__ = """
Basic dispatch
--------------

.. autoclass:: Mapper

    .. automethod:: __call__

    .. method:: rec(expr, *args, **kwargs)

        Identical to :meth:`__call__`, but intended for use in recursive dispatch
        in mapper methods.

    .. automethod:: handle_unsupported_expression

    .. rubric:: Handling objects that don't declare mapper methods

    In particular, this includes many non-subclasses of
    :class:`pymbolic.primitives.Expression`.

    .. automethod:: map_foreign

    These are abstract methods for foreign objects that should be overridden
    in subclasses:

    .. method:: map_constant(expr, *args, **kwargs)

        Mapper method for constants.
        See :func:`pymbolic.primitives.register_constant_class`.

    .. method:: map_list(expr, *args, **kwargs)

    .. method:: map_tuple(expr, *args, **kwargs)

    .. method:: map_numpy_array(expr, *args, **kwargs)

Base classes for new mappers
----------------------------

.. autoclass:: CombineMapper

.. autoclass:: IdentityMapper

.. autoclass:: WalkMapper

.. autoclass:: CSECachingMapperMixin
"""


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
    """A visitor for trees of :class:`pymbolic.primitives.Expression`
    subclasses. Each expression-derived object is dispatched to the
    method named by the :attr:`pymbolic.primitives.Expression.mapper_method`
    attribute.
    """

    def handle_unsupported_expression(self, expr, *args):
        """Mapper method that is invoked for
        :class:`pymbolic.primitives.Expression` subclasses for which a mapper
        method does not exist in this mapper.
        """

        raise UnsupportedExpressionError(
                "%s cannot handle expressions of type %s" % (
                    type(self), type(expr)))

    def __call__(self, expr, *args, **kwargs):
        """Dispatch *expr* to its corresponding mapper method. Pass on
        ``*args`` and ``**kwargs`` unmodified.

        This method is intended as the top-level dispatch entry point and may
        be overridden by subclasses to present a different/more convenient
        interface. :meth:`rec` on the other hand is intended as the recursive
        dispatch method to be used to recurse within mapper method
        implementations.
        """

        try:
            method = getattr(self, expr.mapper_method)
        except AttributeError:
            try:
                method = expr.get_mapper_method(self)
            except AttributeError:
                if isinstance(expr, primitives.Expression):
                    return self.handle_unsupported_expression(
                            expr, *args, **kwargs)
                else:
                    return self.map_foreign(expr, *args, **kwargs)

        return method(expr, *args, **kwargs)

    rec = __call__

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
        """Mapper method dispatch for non-:mod:`pymbolic` objects."""

        if isinstance(expr, primitives.VALID_CONSTANT_CLASSES):
            return self.map_constant(expr, *args)
        elif isinstance(expr, list):
            return self.map_list(expr, *args)
        elif isinstance(expr, tuple):
            return self.map_tuple(expr, *args)
        elif is_numpy_array(expr):
            return self.map_numpy_array(expr, *args)
        else:
            raise ValueError(
                    "%s encountered invalid foreign object: %s" % (
                        self.__class__, repr(expr)))

# }}}


RecursiveMapper = Mapper


# {{{ combine mapper

class CombineMapper(RecursiveMapper):
    """A mapper whose goal it is to *combine* all branches of the expression
    tree into one final result. The default implementation of all mapper
    methods simply recurse (:meth:`Mapper.rec`) on all branches emanating from
    the current expression, and then call :meth:`combine` on a tuple of
    results.

    .. method:: combine(values)

        Combine the mapped results of multiple expressions (given in *values*)
        into a single result, often by summing or taking set unions.

    The :class:`pymbolic.mapper.flop_counter.FlopCounter` is a very simple
    example.  (Look at its source for an idea of how to derive from
    :class:`CombineMapper`.) The
    :class:`pymbolic.mapper.dependency.DependencyMapper` is another example.
    """

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

    def map_left_shift(self, expr, *args):
        return self.combine(
                self.rec(expr.shiftee, *args),
                self.rec(expr.shift, *args))

    map_right_shift = map_left_shift

    def map_bitwise_not(self, expr, *args):
        return self.rec(expr.child, *args)
    map_bitwise_or = map_sum
    map_bitwise_xor = map_sum
    map_bitwise_and = map_sum

    map_logical_not = map_bitwise_not
    map_logical_and = map_sum
    map_logical_or = map_sum

    def map_comparison(self, expr, *args):
        return self.combine((
            self.rec(expr.left, *args),
            self.rec(expr.right, *args)))

    map_max = map_sum
    map_min = map_sum

    def map_list(self, expr, *args):
        return self.combine(self.rec(child, *args) for child in expr)

    map_tuple = map_list

    def map_numpy_array(self, expr, *args):
        return self.combine(self.rec(el) for el in expr.flat)

    def map_multivector(self, expr, *args):
        return self.combine(self.rec(coeff) for bits, coeff in expr.data.iteritems())

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

class IdentityMapper(Mapper):
    """A :class:`Mapper` whose default mapper methods
    make a deep copy of each subexpression.

    See :ref:`custom-manipulation` for an example of the
    manipulations that can be implemented this way.
    """
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

    def map_left_shift(self, expr, *args):
        return type(expr)(
                self.rec(expr.shiftee, *args),
                self.rec(expr.shift, *args))

    map_right_shift = map_left_shift

    def map_bitwise_not(self, expr, *args):
        return type(expr)(
                self.rec(expr.child, *args))

    def map_bitwise_or(self, expr, *args):
        return type(expr)(tuple(
            self.rec(child, *args) for child in expr.children))

    map_bitwise_xor = map_bitwise_or
    map_bitwise_and = map_bitwise_or

    map_logical_not = map_bitwise_not
    map_logical_or = map_bitwise_or
    map_logical_and = map_bitwise_or

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

    def map_multivector(self, expr, *args):
        return expr.map(lambda ch: self.rec(ch, *args))

    def map_common_subexpression(self, expr, *args, **kwargs):
        from pymbolic.primitives import is_zero
        result = self.rec(expr.child, *args, **kwargs)
        if is_zero(result):
            return 0

        return type(expr)(
                result,
                expr.prefix,
                expr.scope,
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
                return self.rec(expr, *args)

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

# }}}


# {{{ walk mapper

class WalkMapper(RecursiveMapper):
    """A mapper whose default mapper method implementations simply recurse
    without propagating any result. Also calls :meth:`visit` for each
    visited subexpression.

    .. method:: visit(expr, *args)
    """
    def map_constant(self, expr, *args):
        self.visit(expr, *args)

    def map_variable(self, expr, *args):
        self.visit(expr, *args)

    def map_function_symbol(self, expr, *args):
        self.visit(expr)

    def map_call(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.function, *args)
        for child in expr.parameters:
            self.rec(child, *args)

    def map_subscript(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.aggregate, *args)
        self.rec(expr.index, *args)

    def map_lookup(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.aggregate, *args)

    def map_sum(self, expr, *args):
        if not self.visit(expr, *args):
            return

        for child in expr.children:
            self.rec(child, *args)

    map_product = map_sum

    def map_quotient(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.numerator, *args)
        self.rec(expr.denominator, *args)

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.base, *args)
        self.rec(expr.exponent, *args)

    def map_polynomial(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.base, *args)
        for exp, coeff in expr.data:
            self.rec(coeff, *args)

    def map_list(self, expr, *args):
        if not self.visit(expr, *args):
            return

        for child in expr:
            self.rec(child, *args)

    map_tuple = map_list

    def map_numpy_array(self, expr, *args):
        if not self.visit(expr, *args):
            return

        from pytools import indices_in_shape
        for i in indices_in_shape(expr.shape):
            self.rec(expr[i], *args)

    def map_common_subexpression(self, expr, *args, **kwargs):
        if not self.visit(expr, *args):
            return

        self.rec(expr.child, *args)

    def map_left_shift(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.shift, *args)
        self.rec(expr.shiftee, *args)

    map_right_shift = map_left_shift

    def map_bitwise_not(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.child, *args)

    map_bitwise_or = map_sum
    map_bitwise_xor = map_sum
    map_bitwise_and = map_sum

    def map_comparison(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.left, *args)
        self.rec(expr.right, *args)

    map_logical_not = map_bitwise_not
    map_logical_and = map_sum
    map_logical_or = map_sum

    def map_if(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.condition, *args)
        self.rec(expr.then, *args)
        self.rec(expr.else_, *args)

    def map_if_positive(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.criterion, *args)
        self.rec(expr.then, *args)
        self.rec(expr.else_, *args)

    def map_substitution(self, expr, *args):
        if not self.visit(expr):
            return

        self.rec(expr.child, *args)
        for v in expr.values:
            self.rec(v, *args)

    def map_derivative(self, expr, *args):
        if not self.visit(expr, *args):
            return

        self.rec(expr.child, *args)

    def visit(self, expr, *args):
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
    map_sum = map_constant
    map_product = map_constant
    map_quotient = map_constant
    map_floor_div = map_constant
    map_remainder = map_constant
    map_power = map_constant

    map_left_shift = map_constant
    map_right_shift = map_constant

    map_bitwise_not = map_constant
    map_bitwise_or = map_constant
    map_bitwise_xor = map_constant
    map_bitwise_and = map_constant

    map_logical_not = map_constant
    map_logical_or = map_constant
    map_logical_and = map_constant

    map_polynomial = map_constant
    map_list = map_constant
    map_tuple = map_constant
    map_numpy_array = map_constant
    map_common_subexpression = map_constant
    map_if_positive = map_constant

# }}}


# {{{ cse caching mixin

class CSECachingMapperMixin(object):
    """A :term:`mix-in` that helps
    subclassed mappers implement caching for
    :class:`pymbolic.primitives.CommonSubexpression`
    instances.

    Instead of the common mapper method for
    :class:`pymbolic.primitives.CommonSubexpression`,
    subclasses should implement the following method:

    .. method:: map_common_subexpression_uncached(expr)

    This method deliberately does not support extra arguments in mapper
    dispatch, to avoid spurious dependencies of the cache on these arguments.
    """

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
