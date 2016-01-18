from __future__ import division
from __future__ import absolute_import
import six
from functools import reduce

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

.. autoclass:: Collector

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

    def handle_unsupported_expression(self, expr, *args, **kwargs):
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
            if isinstance(expr, primitives.Expression):
                return self.handle_unsupported_expression(
                        expr, *args, **kwargs)
            else:
                return self.map_foreign(expr, *args, **kwargs)

        return method(expr, *args, **kwargs)

    rec = __call__

    def map_variable(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_subscript(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_call(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_lookup(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_if_positive(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_rational(self, expr, *args, **kwargs):
        return self.map_quotient(expr, *args, **kwargs)

    def map_foreign(self, expr, *args, **kwargs):
        """Mapper method dispatch for non-:mod:`pymbolic` objects."""

        if isinstance(expr, primitives.VALID_CONSTANT_CLASSES):
            return self.map_constant(expr, *args, **kwargs)
        elif isinstance(expr, list):
            return self.map_list(expr, *args, **kwargs)
        elif isinstance(expr, tuple):
            return self.map_tuple(expr, *args, **kwargs)
        elif is_numpy_array(expr):
            return self.map_numpy_array(expr, *args, **kwargs)
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

    def map_call(self, expr, *args, **kwargs):
        return self.combine(
                (self.rec(expr.function, *args, **kwargs),) +
                tuple(
                    self.rec(child, *args, **kwargs) for child in expr.parameters)
                )

    def map_call_with_kwargs(self, expr, *args, **kwargs):
        return self.combine(
                (self.rec(expr.function, *args, **kwargs),)
                + tuple(
                    self.rec(child, *args, **kwargs)
                    for child in expr.parameters)
                + tuple(
                    self.rec(child, *args, **kwargs)
                    for child in expr.kw_parameters.values())
                )

    def map_subscript(self, expr, *args, **kwargs):
        return self.combine(
                [self.rec(expr.aggregate, *args, **kwargs),
                    self.rec(expr.index, *args, **kwargs)])

    def map_lookup(self, expr, *args, **kwargs):
        return self.rec(expr.aggregate, *args, **kwargs)

    def map_sum(self, expr, *args, **kwargs):
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    map_product = map_sum

    def map_quotient(self, expr, *args, **kwargs):
        return self.combine((
            self.rec(expr.numerator, *args, **kwargs),
            self.rec(expr.denominator, *args, **kwargs)))

    map_floor_div = map_quotient
    map_remainder = map_quotient

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

    def map_left_shift(self, expr, *args, **kwargs):
        return self.combine((
            self.rec(expr.shiftee, *args, **kwargs),
            self.rec(expr.shift, *args, **kwargs)))

    map_right_shift = map_left_shift

    def map_bitwise_not(self, expr, *args, **kwargs):
        return self.rec(expr.child, *args, **kwargs)
    map_bitwise_or = map_sum
    map_bitwise_xor = map_sum
    map_bitwise_and = map_sum

    map_logical_not = map_bitwise_not
    map_logical_and = map_sum
    map_logical_or = map_sum

    def map_comparison(self, expr, *args, **kwargs):
        return self.combine((
            self.rec(expr.left, *args, **kwargs),
            self.rec(expr.right, *args, **kwargs)))

    map_max = map_sum
    map_min = map_sum

    def map_list(self, expr, *args, **kwargs):
        return self.combine(self.rec(child, *args, **kwargs) for child in expr)

    map_tuple = map_list

    def map_numpy_array(self, expr, *args, **kwargs):
        return self.combine(self.rec(el) for el in expr.flat)

    def map_multivector(self, expr, *args, **kwargs):
        return self.combine(
                self.rec(coeff)
                for bits, coeff in six.iteritems(expr.data))

    def map_common_subexpression(self, expr, *args, **kwargs):
        return self.rec(expr.child, *args, **kwargs)

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


# {{{ collector

class Collector(CombineMapper):
    """A subclass of :class:`CombineMapper` for the common purpose of
    collecting data derived from an expression in a set that gets 'unioned'
    across children at each non-leaf node in the expression tree.

    By default, nothing is collected. All leaves return empty sets.

    .. versionadded:: 2014.3
    """

    def combine(self, values):
        import operator
        return reduce(operator.or_, values, set())

    def map_constant(self, expr):
        return set()

    map_variable = map_constant
    map_function_symbol = map_constant

# }}}


# {{{ identity mapper

class IdentityMapper(Mapper):
    """A :class:`Mapper` whose default mapper methods
    make a deep copy of each subexpression.

    See :ref:`custom-manipulation` for an example of the
    manipulations that can be implemented this way.
    """
    def map_constant(self, expr, *args, **kwargs):
        # leaf -- no need to rebuild
        return expr

    def map_variable(self, expr, *args, **kwargs):
        # leaf -- no need to rebuild
        return expr

    def map_function_symbol(self, expr, *args, **kwargs):
        return expr

    def map_call(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.function, *args, **kwargs),
                tuple(self.rec(child, *args, **kwargs)
                    for child in expr.parameters))

    def map_call_with_kwargs(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.function, *args, **kwargs),
                tuple(self.rec(child, *args, **kwargs)
                    for child in expr.parameters),
                dict(
                    (key, self.rec(val, *args, **kwargs))
                    for key, val in six.iteritems(expr.kw_parameters))
                    )

    def map_subscript(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.aggregate, *args, **kwargs),
                self.rec(expr.index, *args, **kwargs))

    def map_lookup(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.aggregate, *args, **kwargs),
                expr.name)

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

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, *args, **kwargs):
        return expr.__class__(self.rec(expr.base, *args, **kwargs),
                              self.rec(expr.exponent, *args, **kwargs))

    def map_polynomial(self, expr, *args, **kwargs):
        return expr.__class__(self.rec(expr.base, *args, **kwargs),
                              ((exp, self.rec(coeff, *args, **kwargs))
                                  for exp, coeff in expr.data))

    def map_left_shift(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.shiftee, *args, **kwargs),
                self.rec(expr.shift, *args, **kwargs))

    map_right_shift = map_left_shift

    def map_bitwise_not(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.child, *args, **kwargs))

    def map_bitwise_or(self, expr, *args, **kwargs):
        return type(expr)(tuple(
            self.rec(child, *args, **kwargs) for child in expr.children))

    map_bitwise_xor = map_bitwise_or
    map_bitwise_and = map_bitwise_or

    map_logical_not = map_bitwise_not
    map_logical_or = map_bitwise_or
    map_logical_and = map_bitwise_or

    def map_comparison(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.left, *args, **kwargs),
                expr.operator,
                self.rec(expr.right, *args, **kwargs))

    def map_list(self, expr, *args, **kwargs):
        return [self.rec(child, *args, **kwargs) for child in expr]

    def map_tuple(self, expr, *args, **kwargs):
        return tuple(self.rec(child, *args, **kwargs) for child in expr)

    def map_numpy_array(self, expr):
        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        from pytools import indices_in_shape
        for i in indices_in_shape(expr.shape):
            result[i] = self.rec(expr[i])
        return result

    def map_multivector(self, expr, *args, **kwargs):
        return expr.map(lambda ch: self.rec(ch, *args, **kwargs))

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

    def map_substitution(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.child, *args, **kwargs),
                expr.variables,
                tuple(self.rec(v, *args, **kwargs) for v in expr.values))

    def map_derivative(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.child, *args, **kwargs),
                expr.variables)

    def map_slice(self, expr, *args, **kwargs):
        def do_map(expr):
            if expr is None:
                return expr
            else:
                return self.rec(expr, *args, **kwargs)

        return type(expr)(
                tuple(do_map(ch) for ch in expr.children))

    def map_if_positive(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.criterion, *args, **kwargs),
                self.rec(expr.then, *args, **kwargs),
                self.rec(expr.else_, *args, **kwargs))

    def map_if(self, expr, *args, **kwargs):
        return type(expr)(
                self.rec(expr.condition, *args, **kwargs),
                self.rec(expr.then, *args, **kwargs),
                self.rec(expr.else_, *args, **kwargs))

    def map_min(self, expr, *args, **kwargs):
        return type(expr)(tuple(
            self.rec(child, *args, **kwargs) for child in expr.children))

    map_max = map_min

# }}}


# {{{ walk mapper

class WalkMapper(RecursiveMapper):
    """A mapper whose default mapper method implementations simply recurse
    without propagating any result. Also calls :meth:`visit` for each
    visited subexpression.

    ``map_...`` methods are required to call :meth:`visit` *before*
        descending to visit their chidlren.

    .. method:: visit(expr, *args, **kwargs)

        Returns *False* if no children of this node should be examined.

    .. method:: post_visit(expr, *args, **kwargs)

        Is called after a node's children are visited.
    """

    def map_constant(self, expr, *args, **kwargs):
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_variable(self, expr, *args, **kwargs):
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_function_symbol(self, expr, *args, **kwargs):
        self.visit(expr)
        self.post_visit(expr, *args, **kwargs)

    def map_call(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.function, *args, **kwargs)
        for child in expr.parameters:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_call_with_kwargs(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.function, *args, **kwargs)
        for child in expr.parameters:
            self.rec(child, *args, **kwargs)

        for child in list(expr.kw_parameters.values()):
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_subscript(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.aggregate, *args, **kwargs)
        self.rec(expr.index, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_lookup(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.aggregate, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_sum(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    map_product = map_sum

    def map_quotient(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.numerator, *args, **kwargs)
        self.rec(expr.denominator, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.base, *args, **kwargs)
        self.rec(expr.exponent, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_polynomial(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.base, *args, **kwargs)
        for exp, coeff in expr.data:
            self.rec(coeff, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_list(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    map_tuple = map_list

    def map_numpy_array(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        from pytools import indices_in_shape
        for i in indices_in_shape(expr.shape):
            self.rec(expr[i], *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_multivector(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        for bits, coeff in six.iteritems(expr.data):
            self.rec(coeff)

        self.post_visit(expr, *args, **kwargs)

    def map_common_subexpression(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_left_shift(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.shift, *args, **kwargs)
        self.rec(expr.shiftee, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    map_right_shift = map_left_shift

    def map_bitwise_not(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    map_bitwise_or = map_sum
    map_bitwise_xor = map_sum
    map_bitwise_and = map_sum

    def map_comparison(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.left, *args, **kwargs)
        self.rec(expr.right, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    map_logical_not = map_bitwise_not
    map_logical_and = map_sum
    map_logical_or = map_sum

    def map_if(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.condition, *args, **kwargs)
        self.rec(expr.then, *args, **kwargs)
        self.rec(expr.else_, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_if_positive(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.criterion, *args, **kwargs)
        self.rec(expr.then, *args, **kwargs)
        self.rec(expr.else_, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    map_min = map_sum
    map_max = map_sum

    def map_substitution(self, expr, *args, **kwargs):
        if not self.visit(expr):
            return

        self.rec(expr.child, *args, **kwargs)
        for v in expr.values:
            self.rec(v, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_derivative(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def visit(self, expr, *args, **kwargs):
        return True

    def post_visit(self, expr, *args, **kwargs):
        pass
# }}}


# {{{ callback mapper

class CallbackMapper(RecursiveMapper):
    def __init__(self, function, fallback_mapper):
        self.function = function
        self.fallback_mapper = fallback_mapper
        fallback_mapper.rec = self.rec

    def map_constant(self, expr, *args, **kwargs):
        return self.function(expr, self, *args, **kwargs)

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


# {{{ caching mixins

class CachingMapperMixin(object):
    def __init__(self):
        super(CachingMapperMixin, self).__init__()
        self.result_cache = {}

    def rec(self, expr):
        try:
            return self.result_cache[expr]
        except TypeError:
            # not hashable, oh well
            return super(CachingMapperMixin, self).rec(expr)
        except KeyError:
            result = super(CachingMapperMixin, self).rec(expr)
            self.result_cache[expr] = result
            return result

    __call__ = rec


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
