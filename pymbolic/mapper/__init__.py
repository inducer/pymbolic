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

from abc import ABC, abstractmethod
from typing import Any, Dict
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


Base classes for mappers with memoization support
-------------------------------------------------

.. autoclass:: CachedMapper

.. autoclass:: CachedIdentityMapper

.. autoclass:: CachedCombineMapper

.. autoclass:: CachedCollector

.. autoclass:: CachedWalkMapper
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

class Mapper:
    """A visitor for trees of :class:`pymbolic.primitives.Expression`
    subclasses. Each expression-derived object is dispatched to the
    method named by the :attr:`pymbolic.primitives.Expression.mapper_method`
    attribute and if not found, the methods named by the class attribute
    *mapper_method* in the method resolution order of the object.
    """

    def handle_unsupported_expression(self, expr, *args, **kwargs):
        """Mapper method that is invoked for
        :class:`pymbolic.primitives.Expression` subclasses for which a mapper
        method does not exist in this mapper.
        """

        raise UnsupportedExpressionError(
                "{} cannot handle expressions of type {}".format(
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

        method_name = getattr(expr, "mapper_method", None)
        if method_name is not None:
            method = getattr(self, method_name, None)
            if method is not None:
                result = method(expr, *args, **kwargs)
                return result

        if isinstance(expr, primitives.Expression):
            for cls in type(expr).__mro__[1:]:
                method_name = getattr(cls, "mapper_method", None)
                if method_name:
                    method = getattr(self, method_name, None)
                    if method:
                        return method(expr, *args, **kwargs)
            else:
                return self.handle_unsupported_expression(expr, *args, **kwargs)
        else:
            return self.map_foreign(expr, *args, **kwargs)

    rec = __call__

    def rec_fallback(self, expr, *args, **kwargs):
        if isinstance(expr, primitives.Expression):
            for cls in type(expr).__mro__[1:]:
                method_name = getattr(cls, "mapper_method", None)
                if method_name:
                    method = getattr(self, method_name, None)
                    if method:
                        return method(expr, *args, **kwargs)
            else:
                return self.handle_unsupported_expression(expr, *args, **kwargs)
        else:
            return self.map_foreign(expr, *args, **kwargs)

    def map_algebraic_leaf(self, expr, *args, **kwargs):
        raise NotImplementedError

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

    def map_quotient(self, expr, *args, **kwargs):
        raise NotImplementedError

    def map_constant(self, expr, *args, **kwargs):
        raise NotImplementedError

    def map_list(self, expr, *args, **kwargs):
        raise NotImplementedError

    def map_tuple(self, expr, *args, **kwargs):
        raise NotImplementedError

    def map_numpy_array(self, expr, *args, **kwargs):
        raise NotImplementedError

    def map_nan(self, expr, *args, **kwargs):
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_foreign(self, expr, *args, **kwargs):
        """Mapper method dispatch for non-:mod:`pymbolic` objects."""

        if isinstance(expr, primitives.VALID_CONSTANT_CLASSES):
            return self.map_constant(expr, *args, **kwargs)
        elif is_numpy_array(expr):
            return self.map_numpy_array(expr, *args, **kwargs)
        elif isinstance(expr, list):
            return self.map_list(expr, *args, **kwargs)
        elif isinstance(expr, tuple):
            return self.map_tuple(expr, *args, **kwargs)
        else:
            raise ValueError(
                    "{} encountered invalid foreign object: {}".format(
                        self.__class__, repr(expr)))


_NOT_IN_CACHE = object()


class CachedMapper(Mapper):
    """
    A mapper that memoizes the mapped result for the expressions traversed.

    .. automethod:: get_cache_key
    """
    def __init__(self):
        self._cache: Dict[Any, Any] = {}
        Mapper.__init__(self)

    def get_cache_key(self, expr, *args, **kwargs):
        """
        Returns the key corresponding to which the result of a mapper method is
        stored in the cache.

        .. warning::

            Assumes that elements of *args* and *kwargs* are immutable, and that
            *self* does not store any mutable state. Derived mappers must
            override this method.
        """
        # Must add 'type(expr)', to differentiate between python scalar types.
        # In Python, the following conditions are true: "hash(4) == hash(4.0)"
        # and "4 == 4.0", but their traversal results cannot be re-used.
        return (type(expr), expr, args, tuple(sorted(kwargs.items())))

    def __call__(self, expr, *args, **kwargs):
        result = self._cache.get(
                (cache_key := self.get_cache_key(expr, *args, **kwargs)),
                _NOT_IN_CACHE)
        if result is not _NOT_IN_CACHE:
            return result

        method_name = getattr(expr, "mapper_method", None)
        if method_name is not None:
            method = getattr(self, method_name, None)
            if method is not None:
                result = method(expr, *args, **kwargs)
                self._cache[cache_key] = result
                return result

        result = self.rec_fallback(expr, *args, **kwargs)
        self._cache[cache_key] = result
        return result

    rec = __call__

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

    def combine(self, values):
        raise NotImplementedError

    def map_call(self, expr, *args, **kwargs):
        return self.combine(
                (self.rec(expr.function, *args, **kwargs),)
                + tuple([
                    self.rec(child, *args, **kwargs) for child in expr.parameters
                    ])
                )

    def map_call_with_kwargs(self, expr, *args, **kwargs):
        return self.combine(
                (self.rec(expr.function, *args, **kwargs),)
                + tuple([
                    self.rec(child, *args, **kwargs)
                    for child in expr.parameters])
                + tuple([
                    self.rec(child, *args, **kwargs)
                    for child in expr.kw_parameters.values()])
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
                (self.rec(expr.base, *args, **kwargs),)
                + tuple([
                    self.rec(coeff, *args, **kwargs) for exp, coeff in expr.data
                    ])
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
        return self.combine(self.rec(el, *args, **kwargs) for el in expr.flat)

    def map_multivector(self, expr, *args, **kwargs):
        return self.combine(
                self.rec(coeff, *args, **kwargs)
                for bits, coeff in expr.data.items())

    def map_common_subexpression(self, expr, *args, **kwargs):
        return self.rec(expr.child, *args, **kwargs)

    def map_if_positive(self, expr, *args, **kwargs):
        return self.combine([
            self.rec(expr.criterion, *args, **kwargs),
            self.rec(expr.then, *args, **kwargs),
            self.rec(expr.else_, *args, **kwargs)])

    def map_if(self, expr, *args, **kwargs):
        return self.combine([
            self.rec(expr.condition, *args, **kwargs),
            self.rec(expr.then, *args, **kwargs),
            self.rec(expr.else_, *args, **kwargs)])


class CachedCombineMapper(CachedMapper, CombineMapper):
    pass

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
        from functools import reduce
        return reduce(operator.or_, values, set())

    def map_constant(self, expr, *args, **kwargs):
        return set()

    map_variable = map_constant
    map_wildcard = map_constant
    map_dot_wildcard = map_constant
    map_star_wildcard = map_constant
    map_function_symbol = map_constant


class CachedCollector(CachedMapper, Collector):
    pass

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

    def map_wildcard(self, expr, *args, **kwargs):
        return expr

    def map_dot_wildcard(self, expr, *args, **kwargs):
        return expr

    def map_star_wildcard(self, expr, *args, **kwargs):
        return expr

    def map_function_symbol(self, expr, *args, **kwargs):
        return expr

    def map_call(self, expr, *args, **kwargs):
        function = self.rec(expr.function, *args, **kwargs)
        parameters = tuple([
            self.rec(child, *args, **kwargs) for child in expr.parameters
            ])
        if (function is expr.function
            and all(child is orig_child
                for child, orig_child in zip(expr.parameters, parameters))):
            return expr

        return type(expr)(function, parameters)

    def map_call_with_kwargs(self, expr, *args, **kwargs):
        function = self.rec(expr.function, *args, **kwargs)
        parameters = tuple([
            self.rec(child, *args, **kwargs) for child in expr.parameters
            ])
        kw_parameters = {
                key: self.rec(val, *args, **kwargs)
                for key, val in expr.kw_parameters.items()}

        if (function is expr.function
            and all(child is orig_child for child, orig_child in
                zip(parameters, expr.parameters))
                and all(kw_parameters[k] is v for k, v in
                        expr.kw_parameters.items())):
            return expr
        return type(expr)(function, parameters, kw_parameters)

    def map_subscript(self, expr, *args, **kwargs):
        aggregate = self.rec(expr.aggregate, *args, **kwargs)
        index = self.rec(expr.index, *args, **kwargs)
        if aggregate is expr.aggregate and index is expr.index:
            return expr
        return type(expr)(aggregate, index)

    def map_lookup(self, expr, *args, **kwargs):
        aggregate = self.rec(expr.aggregate, *args, **kwargs)
        if aggregate is expr.aggregate:
            return expr
        return type(expr)(aggregate, expr.name)

    def map_sum(self, expr, *args, **kwargs):
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children)):
            return expr

        return type(expr)(tuple(children))

    map_product = map_sum

    def map_quotient(self, expr, *args, **kwargs):
        numerator = self.rec(expr.numerator, *args, **kwargs)
        denominator = self.rec(expr.denominator, *args, **kwargs)
        if numerator is expr.numerator and denominator is expr.denominator:
            return expr
        return expr.__class__(numerator, denominator)

    map_floor_div = map_quotient
    map_remainder = map_quotient

    def map_power(self, expr, *args, **kwargs):
        base = self.rec(expr.base, *args, **kwargs)
        exponent = self.rec(expr.exponent, *args, **kwargs)
        if base is expr.base and exponent is expr.exponent:
            return expr
        return expr.__class__(base, exponent)

    def map_polynomial(self, expr, *args, **kwargs):
        base = self.rec(expr.base, *args, **kwargs)
        data = ((exp, self.rec(coeff, *args, **kwargs))
                                  for exp, coeff in expr.data)
        if base is expr.base and all(
                t[1] is orig_t[1] for t, orig_t in zip(data, expr.data)):
            return expr
        return expr.__class__(base, data)

    def map_left_shift(self, expr, *args, **kwargs):
        shiftee = self.rec(expr.shiftee, *args, **kwargs)
        shift = self.rec(expr.shift, *args, **kwargs)
        if shiftee is expr.shiftee and shift is expr.shift:
            return expr
        return type(expr)(shiftee, shift)

    map_right_shift = map_left_shift

    def map_bitwise_not(self, expr, *args, **kwargs):
        child = self.rec(expr.child, *args, **kwargs)
        if child is expr.child:
            return expr
        return type(expr)(child)

    def map_bitwise_or(self, expr, *args, **kwargs):
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children)):
            return expr

        return type(expr)(tuple(children))

    map_bitwise_xor = map_bitwise_or
    map_bitwise_and = map_bitwise_or

    map_logical_not = map_bitwise_not
    map_logical_or = map_bitwise_or
    map_logical_and = map_bitwise_or

    def map_comparison(self, expr, *args, **kwargs):
        left = self.rec(expr.left, *args, **kwargs)
        right = self.rec(expr.right, *args, **kwargs)
        if left is expr.left and right is expr.right:
            return expr

        return type(expr)(left, expr.operator, right)

    def map_list(self, expr, *args, **kwargs):
        return [self.rec(child, *args, **kwargs) for child in expr]

    def map_tuple(self, expr, *args, **kwargs):
        children = [self.rec(child, *args, **kwargs) for child in expr]
        if all(child is orig_child
                for child, orig_child in zip(children, expr)):
            return expr

        return tuple(children)

    def map_numpy_array(self, expr, *args, **kwargs):
        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        for i in numpy.ndindex(expr.shape):
            result[i] = self.rec(expr[i], *args, **kwargs)
        return result

    def map_multivector(self, expr, *args, **kwargs):
        return expr.map(lambda ch: self.rec(ch, *args, **kwargs))

    def map_common_subexpression(self, expr, *args, **kwargs):
        from pymbolic.primitives import is_zero
        result = self.rec(expr.child, *args, **kwargs)
        if is_zero(result):
            return 0
        if result is expr.child:
            return expr

        return type(expr)(
                result,
                expr.prefix,
                expr.scope,
                **expr.get_extra_properties())

    def map_substitution(self, expr, *args, **kwargs):
        child = self.rec(expr.child, *args, **kwargs)
        values = tuple([self.rec(v, *args, **kwargs) for v in expr.values])
        if child is expr.child and all([val is orig_val
                for val, orig_val in zip(values, expr.values)]):
            return expr

        return type(expr)(child, expr.variables, values)

    def map_derivative(self, expr, *args, **kwargs):
        child = self.rec(expr.child, *args, **kwargs)
        if child is expr.child:
            return expr

        return type(expr)(child, expr.variables)

    def map_slice(self, expr, *args, **kwargs):
        children = tuple([
            None if child is None else self.rec(child, *args, **kwargs)
            for child in expr.children
            ])
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children)):
            return expr

        return type(expr)(children)

    def map_if_positive(self, expr, *args, **kwargs):
        criterion = self.rec(expr.criterion, *args, **kwargs)
        then = self.rec(expr.then, *args, **kwargs)
        else_ = self.rec(expr.else_, *args, **kwargs)
        if criterion is expr.criterion \
                and then is expr.then \
                and else_ is expr.else_:
            return expr

        return type(expr)(criterion, then, else_)

    def map_if(self, expr, *args, **kwargs):
        condition = self.rec(expr.condition, *args, **kwargs)
        then = self.rec(expr.then, *args, **kwargs)
        else_ = self.rec(expr.else_, *args, **kwargs)
        if condition is expr.condition \
                and then is expr.then \
                and else_ is expr.else_:
            return expr

        return type(expr)(condition, then, else_)

    def map_min(self, expr, *args, **kwargs):
        children = tuple([
            self.rec(child, *args, **kwargs) for child in expr.children
            ])
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children)):
            return expr

        return type(expr)(children)

    map_max = map_min

    def map_nan(self, expr, *args, **kwargs):
        # Leaf node -- don't recurse
        return expr


class CachedIdentityMapper(CachedMapper, IdentityMapper):
    pass

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

    map_wildcard = map_variable
    map_dot_wildcard = map_variable
    map_star_wildcard = map_variable
    map_function_symbol = map_variable
    map_nan = map_variable

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
        for _exp, coeff in expr.data:
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

        import numpy
        for i in numpy.ndindex(expr.shape):
            self.rec(expr[i], *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_multivector(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        for _bits, coeff in expr.data.items():
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

    def map_slice(self, expr, *args, **kwargs):
        if not self.visit(expr, *args, **kwargs):
            return

        if expr.start is not None:
            self.rec(expr.start, *args, **kwargs)
        if expr.stop is not None:
            self.rec(expr.stop, *args, **kwargs)
        if expr.step is not None:
            self.rec(expr.step, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def visit(self, expr, *args, **kwargs):
        return True

    def post_visit(self, expr, *args, **kwargs):
        pass


class CachedWalkMapper(CachedMapper, WalkMapper):
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
    map_if = map_constant
    map_comparison = map_constant

# }}}


# {{{ caching mixins

class CachingMapperMixin:
    def __init__(self):
        super().__init__()
        self.result_cache = {}

        from warnings import warn
        warn("CachingMapperMixin is deprecated and will be removed "
                "in version 2023.x. Use CachedMapper instead.",
                DeprecationWarning, stacklevel=2)

    def rec(self, expr):
        try:
            return self.result_cache[expr]
        except TypeError:
            # not hashable, oh well
            method_name = getattr(expr, "mapper_method", None)
            if method_name is not None:
                method = getattr(self, method_name, None)
                if method is not None:
                    return method(expr, )
            return super().rec(expr)
        except KeyError:
            method_name = getattr(expr, "mapper_method", None)
            if method_name is not None:
                method = getattr(self, method_name, None)
                if method is not None:
                    result = method(expr, )
                    self.result_cache[expr] = result
                    return result

            result = super().rec(expr)
            self.result_cache[expr] = result
            return result

    __call__ = rec


class CSECachingMapperMixin(ABC):
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

    def map_common_subexpression(self, expr, *args):
        try:
            ccd = self._cse_cache_dict
        except AttributeError:
            ccd = self._cse_cache_dict = {}

        try:
            return ccd[(expr, *args)]
        except KeyError:
            result = self.map_common_subexpression_uncached(expr, *args)
            ccd[(expr, *args)] = result
            return result

    @abstractmethod
    def map_common_subexpression_uncached(self, expr, *args):
        pass

# }}}

# vim: foldmethod=marker
