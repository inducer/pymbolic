from __future__ import annotations


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
from collections.abc import Callable, Hashable, Iterable, Mapping, Set
from typing import (
    TYPE_CHECKING,
    Concatenate,
    Generic,
    TypeAlias,
    TypeVar,
    cast,
)
from warnings import warn

from immutabledict import immutabledict
from typing_extensions import ParamSpec, TypeIs

import pymbolic.primitives as p
from pymbolic.typing import ArithmeticExpression, Expression


if TYPE_CHECKING:
    import numpy as np

    from pymbolic.geometric_algebra import MultiVector
    from pymbolic.rational import Rational


__doc__ = """
Basic dispatch
--------------

.. class:: ResultT

    A type variable for the result returned by a :class:`Mapper`.

.. autoclass:: Mapper

    .. automethod:: __call__

    .. method:: rec(expr, *args, **kwargs)

        Identical to :meth:`__call__`, but intended for use in recursive dispatch
        in mapper methods.

    .. automethod:: handle_unsupported_expression

    .. rubric:: Handling objects that don't declare mapper methods

    In particular, this includes many non-subclasses of
    :class:`pymbolic.ExpressionNode`.

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


if TYPE_CHECKING:
    import numpy as np

    def is_numpy_array(val) -> TypeIs[np.ndarray]:
        return isinstance(val, np.ndarray)
else:
    try:
        import numpy as np

        def is_numpy_array(val):
            return isinstance(val, np.ndarray)
    except ImportError:
        def is_numpy_array(ary):
            return False


class UnsupportedExpressionError(ValueError):
    pass


# {{{ mapper base

ResultT = TypeVar("ResultT")

# This ParamSpec could be marked contravariant (just like Callable is contravariant
# in its arguments). As of mypy 1.14/Py3.13 (Nov 2024), mypy complains of as-yet
# undefined semantics, so it's probably too soon.
P = ParamSpec("P")


class Mapper(Generic[ResultT, P]):
    """A visitor for trees of :class:`pymbolic.ExpressionNode`
    subclasses. Each expression-derived object is dispatched to the
    method named by the :attr:`pymbolic.ExpressionNode.mapper_method`
    attribute and if not found, the methods named by the class attribute
    *mapper_method* in the method resolution order of the object.

    ..automethod:: handle_unsupported_expression
    ..automethod:: __call__
    ..automethod:: rec
    """

    def handle_unsupported_expression(self,
            expr: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        """Mapper method that is invoked for
        :class:`pymbolic.ExpressionNode` subclasses for which a mapper
        method does not exist in this mapper.
        """

        raise UnsupportedExpressionError(
                "{} cannot handle expressions of type {}".format(
                    type(self), type(expr)))

    def __call__(self,
             expr: Expression, *args: P.args, **kwargs: P.kwargs) -> ResultT:
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

        if isinstance(expr, p.ExpressionNode):
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

    def rec_fallback(self,
            expr: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        if isinstance(expr, p.ExpressionNode):
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

    def map_algebraic_leaf(self,
            expr: p.AlgebraicLeaf,
            *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_variable(self,
            expr: p.Variable, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_subscript(self,
            expr: p.Subscript, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_call(self,
            expr: p.Call, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_call_with_kwargs(self,
            expr: p.CallWithKwargs,
            *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_lookup(self,
            expr: p.Lookup, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_if(self,
            expr: p.If, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_sum(self,
            expr: p.Sum, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_product(self,
            expr: p.Product, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_rational(self,
            expr: Rational, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_quotient(self,
            expr: p.Quotient, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_floor_div(self,
            expr: p.FloorDiv, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_remainder(self,
            expr: p.Remainder, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_constant(self,
            expr: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_comparison(self,
            expr: p.Comparison, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_min(self,
            expr: p.Min, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_max(self,
            expr: p.Max, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_list(self,
            expr: list[Expression], *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_tuple(self,
            expr: tuple[Expression, ...],
            *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_numpy_array(self,
            expr: np.ndarray, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        raise NotImplementedError

    def map_left_shift(self,
            expr: p.LeftShift, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_right_shift(self,
                expr: p.RightShift, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_bitwise_not(self,
                expr: p.BitwiseNot, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_bitwise_or(self,
                expr: p.BitwiseOr, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_bitwise_and(self,
                expr: p.BitwiseAnd, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_bitwise_xor(self,
                expr: p.BitwiseXor, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_logical_not(self,
                expr: p.LogicalNot, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_logical_or(self,
                expr: p.LogicalOr, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_logical_and(self,
                expr: p.LogicalAnd, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        raise NotImplementedError

    def map_nan(self,
                expr: p.NaN,
                *args: P.args,
                **kwargs: P.kwargs
            ) -> ResultT:
        return self.map_algebraic_leaf(expr, *args, **kwargs)

    def map_foreign(self,
                expr: object,
                *args: P.args,
                **kwargs: P.kwargs
            ) -> ResultT:
        """Mapper method dispatch for non-:mod:`pymbolic` objects."""

        if isinstance(expr, p.VALID_CONSTANT_CLASSES):
            return self.map_constant(expr, *args, **kwargs)
        elif is_numpy_array(expr):
            return self.map_numpy_array(expr, *args, **kwargs)
        elif isinstance(expr, tuple):
            return self.map_tuple(expr, *args, **kwargs)
        elif isinstance(expr, list):
            warn("List found in expression graph. "
                 "This is deprecated and will stop working in 2025. "
                 "Use tuples instead.", DeprecationWarning, stacklevel=2
             )
            return self.map_list(expr, *args, **kwargs)
        else:
            raise ValueError(
                    "{} encountered invalid foreign object: {}".format(
                        self.__class__, repr(expr)))


class _NotInCache:
    pass


CacheKeyT: TypeAlias = Hashable


class CachedMapper(Mapper[ResultT, P]):
    """
    A mapper that memoizes the mapped result for the expressions traversed.

    .. automethod:: get_cache_key
    """
    def __init__(self) -> None:
        self._cache: dict[CacheKeyT, ResultT] = {}
        Mapper.__init__(self)

    def get_cache_key(self,
              expr: Expression,
              *args: P.args,
              **kwargs: P.kwargs
          ) -> CacheKeyT:
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
        return (type(expr), expr, args, immutabledict(kwargs))

    def __call__(self,
                 expr: Expression,
                 *args: P.args,
                 **kwargs: P.kwargs
             ) -> ResultT:
        result = self._cache.get(
                (cache_key := self.get_cache_key(expr, *args, **kwargs)),
                _NotInCache)
        if not isinstance(result, type):
            return result

        method_name = getattr(expr, "mapper_method", None)
        if method_name is not None:
            method = cast(
                Callable[Concatenate[Expression, P], ResultT] | None,
                getattr(self, method_name, None)
                )
            if method is not None:
                result = method(expr, *args, **kwargs)
                self._cache[cache_key] = result
                return result

        result = self.rec_fallback(expr, *args, **kwargs)
        self._cache[cache_key] = result
        return result

    rec = __call__

# }}}


# {{{ combine mapper

class CombineMapper(Mapper[ResultT, P]):
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

    def combine(self, values: Iterable[ResultT]) -> ResultT:
        raise NotImplementedError

    def map_call(self,
            expr: p.Call, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
            self.rec(expr.function, *args, **kwargs),
            *[self.rec(child, *args, **kwargs) for child in expr.parameters]
            ))

    def map_call_with_kwargs(self,
            expr: p.CallWithKwargs,
            *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
            self.rec(expr.function, *args, **kwargs),
            *[self.rec(child, *args, **kwargs) for child in expr.parameters],
            *[self.rec(child, *args, **kwargs)
              for child in expr.kw_parameters.values()]
            ))

    def map_subscript(self,
            expr: p.Subscript, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(
                [self.rec(expr.aggregate, *args, **kwargs),
                    self.rec(expr.index, *args, **kwargs)])

    def map_lookup(self,
            expr: p.Lookup, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.rec(expr.aggregate, *args, **kwargs)

    def map_sum(self,
            expr: p.Sum, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_product(self,
            expr: p.Product, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_quotient(self,
            expr: p.Quotient, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
            self.rec(expr.numerator, *args, **kwargs),
            self.rec(expr.denominator, *args, **kwargs)))

    def map_floor_div(self,
            expr: p.FloorDiv, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
            self.rec(expr.numerator, *args, **kwargs),
            self.rec(expr.denominator, *args, **kwargs)))

    def map_remainder(self,
            expr: p.Remainder, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
            self.rec(expr.numerator, *args, **kwargs),
            self.rec(expr.denominator, *args, **kwargs)))

    def map_power(self,
            expr: p.Power, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
                self.rec(expr.base, *args, **kwargs),
                self.rec(expr.exponent, *args, **kwargs)))

    def map_left_shift(self,
            expr: p.LeftShift, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
            self.rec(expr.shiftee, *args, **kwargs),
            self.rec(expr.shift, *args, **kwargs)))

    def map_right_shift(self,
            expr: p.RightShift, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
            self.rec(expr.shiftee, *args, **kwargs),
            self.rec(expr.shift, *args, **kwargs)))

    def map_bitwise_not(self,
            expr: p.BitwiseNot, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.rec(expr.child, *args, **kwargs)

    def map_bitwise_or(self,
            expr: p.BitwiseOr, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_bitwise_and(self,
            expr: p.BitwiseAnd, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_bitwise_xor(self,
            expr: p.BitwiseXor, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_logical_not(self,
            expr: p.LogicalNot, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.rec(expr.child, *args, **kwargs)

    def map_logical_or(self,
            expr: p.LogicalOr, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_logical_and(self,
            expr: p.LogicalAnd, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_comparison(self,
            expr: p.Comparison, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine((
            self.rec(expr.left, *args, **kwargs),
            self.rec(expr.right, *args, **kwargs)))

    def map_max(self,
            expr: p.Max, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_min(self,
            expr: p.Min, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs)
                for child in expr.children)

    def map_tuple(self,
                expr: tuple[Expression, ...], *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs) for child in expr)

    def map_list(self,
                expr: list[Expression], *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        return self.combine(self.rec(child, *args, **kwargs) for child in expr)

    def map_numpy_array(self,
                expr: np.ndarray, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        return self.combine(self.rec(el, *args, **kwargs) for el in expr.flat)

    def map_multivector(self,
                expr: MultiVector[ArithmeticExpression],
                *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        return self.combine(
                self.rec(coeff, *args, **kwargs)
                for bits, coeff in expr.data.items())

    def map_common_subexpression(self,
                expr: p.CommonSubexpression, *args: P.args, **kwargs: P.kwargs
            ) -> ResultT:
        return self.rec(expr.child, *args, **kwargs)

    def map_if(self,
            expr: p.If, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.combine([
            self.rec(expr.condition, *args, **kwargs),
            self.rec(expr.then, *args, **kwargs),
            self.rec(expr.else_, *args, **kwargs)])


class CachedCombineMapper(CachedMapper, CombineMapper):
    pass

# }}}


# {{{ collector

CollectedT = TypeVar("CollectedT")


class Collector(CombineMapper[Set[CollectedT], P]):
    """A subclass of :class:`CombineMapper` for the common purpose of
    collecting data derived from an expression in a set that gets 'unioned'
    across children at each non-leaf node in the expression tree.

    By default, nothing is collected. All leaves return empty sets.

    .. versionadded:: 2014.3
    """

    def combine(self,
                values: Iterable[Set[CollectedT]]
            ) -> Set[CollectedT]:
        import operator
        from functools import reduce
        return reduce(operator.or_, values, set())

    def map_constant(self, expr: object,
                     *args: P.args, **kwargs: P.kwargs) -> Set[CollectedT]:
        return set()

    def map_variable(self, expr: p.Variable,
                     *args: P.args, **kwargs: P.kwargs) -> Set[CollectedT]:
        return set()

    def map_wildcard(self, expr: p.Wildcard,
                     *args: P.args, **kwargs: P.kwargs) -> Set[CollectedT]:
        return set()

    def map_dot_wildcard(self, expr: p.DotWildcard,
                     *args: P.args, **kwargs: P.kwargs) -> Set[CollectedT]:
        return set()

    def map_star_wildcard(self, expr: p.StarWildcard,
                     *args: P.args, **kwargs: P.kwargs) -> Set[CollectedT]:
        return set()

    def map_function_symbol(self, expr: p.FunctionSymbol,
                     *args: P.args, **kwargs: P.kwargs) -> Set[CollectedT]:
        return set()


class CachedCollector(CachedMapper, Collector):
    pass

# }}}


# {{{ identity mapper

class IdentityMapper(Mapper[Expression, P]):
    """A :class:`Mapper` whose default mapper methods
    make a deep copy of each subexpression.

    See :ref:`custom-manipulation` for an example of the
    manipulations that can be implemented this way.

    .. automethod:: rec_arith
    """

    def rec_arith(self,
                expr: ArithmeticExpression, *args: P.args, **kwargs: P.kwargs
            ) -> ArithmeticExpression:
        res = self.rec(expr, *args, **kwargs)
        assert p.is_arithmetic_expression(res)
        return res

    def map_constant(self,
                expr: object, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        # leaf -- no need to rebuild
        assert p.is_valid_operand(expr)
        return expr

    def map_variable(self,
                expr: p.Variable, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        # leaf -- no need to rebuild
        return expr

    def map_wildcard(self,
                expr: p.Wildcard, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        return expr

    def map_dot_wildcard(self,
                expr: p.DotWildcard, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        return expr

    def map_star_wildcard(self,
                expr: p.StarWildcard, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        return expr

    def map_function_symbol(self,
                expr: p.FunctionSymbol, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        return expr

    def map_call(self,
                expr: p.Call, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        function = self.rec(expr.function, *args, **kwargs)
        parameters = tuple([
            self.rec(child, *args, **kwargs) for child in expr.parameters
            ])
        if (function is expr.function
            and all(child is orig_child
                for child, orig_child in zip(
                            expr.parameters, parameters, strict=True))):
            return expr

        return type(expr)(function, parameters)

    def map_call_with_kwargs(self,
                expr: p.CallWithKwargs, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        function = self.rec(expr.function, *args, **kwargs)
        parameters = tuple([
            self.rec(child, *args, **kwargs) for child in expr.parameters
            ])
        kw_parameters: Mapping[str, Expression] = immutabledict({
                key: self.rec(val, *args, **kwargs)
                for key, val in expr.kw_parameters.items()})

        if (function is expr.function
            and all(child is orig_child for child, orig_child in
                zip(parameters, expr.parameters, strict=True))
                and all(kw_parameters[k] is v for k, v in
                        expr.kw_parameters.items())):
            return expr
        return type(expr)(function, parameters, kw_parameters)

    def map_subscript(self,
                expr: p.Subscript, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        aggregate = self.rec(expr.aggregate, *args, **kwargs)
        index = self.rec(expr.index, *args, **kwargs)
        if aggregate is expr.aggregate and index is expr.index:
            return expr
        return type(expr)(aggregate, index)

    def map_lookup(self,
                expr: p.Lookup, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        aggregate = self.rec(expr.aggregate, *args, **kwargs)
        if aggregate is expr.aggregate:
            return expr
        return type(expr)(aggregate, expr.name)

    def map_sum(self,
                expr: p.Sum, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(tuple(children))

    def map_product(self,
                expr: p.Product, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(tuple(children))

    def map_quotient(self,
                expr: p.Quotient, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        numerator = self.rec_arith(expr.numerator, *args, **kwargs)
        denominator = self.rec_arith(expr.denominator, *args, **kwargs)
        if numerator is expr.numerator and denominator is expr.denominator:
            return expr
        return expr.__class__(numerator, denominator)

    def map_floor_div(self,
                expr: p.FloorDiv, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        numerator = self.rec_arith(expr.numerator, *args, **kwargs)
        denominator = self.rec_arith(expr.denominator, *args, **kwargs)
        if numerator is expr.numerator and denominator is expr.denominator:
            return expr
        return expr.__class__(numerator, denominator)

    def map_remainder(self,
                expr: p.Remainder, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        numerator = self.rec_arith(expr.numerator, *args, **kwargs)
        denominator = self.rec_arith(expr.denominator, *args, **kwargs)
        if numerator is expr.numerator and denominator is expr.denominator:
            return expr
        return expr.__class__(numerator, denominator)

    def map_power(self,
                expr: p.Power, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        base = self.rec_arith(expr.base, *args, **kwargs)
        exponent = self.rec_arith(expr.exponent, *args, **kwargs)
        if base is expr.base and exponent is expr.exponent:
            return expr
        return expr.__class__(base, exponent)

    def map_left_shift(self,
                expr: p.LeftShift, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        shiftee = self.rec(expr.shiftee, *args, **kwargs)
        shift = self.rec(expr.shift, *args, **kwargs)
        if shiftee is expr.shiftee and shift is expr.shift:
            return expr
        return type(expr)(shiftee, shift)

    def map_right_shift(self,
                expr: p.RightShift, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        shiftee = self.rec(expr.shiftee, *args, **kwargs)
        shift = self.rec(expr.shift, *args, **kwargs)
        if shiftee is expr.shiftee and shift is expr.shift:
            return expr
        return type(expr)(shiftee, shift)

    def map_bitwise_not(self,
                expr: p.BitwiseNot, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        child = self.rec(expr.child, *args, **kwargs)
        if child is expr.child:
            return expr
        return type(expr)(child)

    def map_bitwise_or(self,
                expr: p.BitwiseOr, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(tuple(children))

    def map_bitwise_and(self,
                expr: p.BitwiseAnd, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(tuple(children))

    def map_bitwise_xor(self,
                expr: p.BitwiseXor, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(tuple(children))

    def map_logical_not(self,
                expr: p.LogicalNot, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        child = self.rec(expr.child, *args, **kwargs)
        if child is expr.child:
            return expr
        return type(expr)(child)

    def map_logical_or(self,
                expr: p.LogicalOr, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(tuple(children))

    def map_logical_and(self,
                expr: p.LogicalAnd, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        children = [self.rec(child, *args, **kwargs) for child in expr.children]
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(tuple(children))

    def map_comparison(self,
                expr: p.Comparison, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        left = self.rec(expr.left, *args, **kwargs)
        right = self.rec(expr.right, *args, **kwargs)
        if left is expr.left and right is expr.right:
            return expr

        return type(expr)(left, expr.operator, right)

    def map_list(self,
                expr: list[Expression], *args: P.args, **kwargs: P.kwargs
            ) -> Expression:

        # True fact: lists aren't expressions
        return [self.rec(child, *args, **kwargs) for child in expr]  # type: ignore[return-value]

    def map_tuple(self,
                expr: tuple[Expression, ...], *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        children = [self.rec(child, *args, **kwargs) for child in expr]
        if all(child is orig_child
                for child, orig_child in zip(children, expr, strict=True)):
            return expr

        return tuple(children)

    def map_numpy_array(self,
                expr: np.ndarray, *args: P.args, **kwargs: P.kwargs
            ) -> Expression:

        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        for i in numpy.ndindex(expr.shape):
            result[i] = self.rec(expr[i], *args, **kwargs)

        # True fact: ndarrays aren't expressions
        return result  # type: ignore[return-value]

    def map_multivector(self,
                expr: MultiVector[ArithmeticExpression],
                *args: P.args, **kwargs: P.kwargs
            ) -> Expression:
        # True fact: MultiVectors aren't expressions
        return expr.map(lambda ch: cast(ArithmeticExpression,
                                        self.rec(ch, *args, **kwargs)))  # type: ignore[return-value]

    def map_common_subexpression(self,
                expr: p.CommonSubexpression,
                *args: P.args, **kwargs: P.kwargs) -> Expression:
        result = self.rec(expr.child, *args, **kwargs)
        if result is expr.child:
            return expr

        return type(expr)(
                result,
                expr.prefix,
                expr.scope,
                **expr.get_extra_properties())

    def map_substitution(self,
                 expr: p.Substitution,
                 *args: P.args, **kwargs: P.kwargs) -> Expression:
        child = self.rec(expr.child, *args, **kwargs)
        values = tuple([self.rec(v, *args, **kwargs) for v in expr.values])
        if child is expr.child and all(val is orig_val
                for val, orig_val in zip(values, expr.values, strict=True)):
            return expr

        return type(expr)(child, expr.variables, values)

    def map_derivative(self,
                expr: p.Derivative,
                *args: P.args, **kwargs: P.kwargs) -> Expression:
        child = self.rec(expr.child, *args, **kwargs)
        if child is expr.child:
            return expr

        return type(expr)(child, expr.variables)

    def map_slice(self,
                expr: p.Slice,
                *args: P.args, **kwargs: P.kwargs) -> Expression:
        children: p.SliceChildrenT = cast(p.SliceChildrenT, tuple([
            None if child is None else self.rec(child, *args, **kwargs)
            for child in expr.children
            ]))
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(children)

    def map_if(self, expr: p.If, *args: P.args, **kwargs: P.kwargs) -> Expression:
        condition = self.rec(expr.condition, *args, **kwargs)
        then = self.rec(expr.then, *args, **kwargs)
        else_ = self.rec(expr.else_, *args, **kwargs)
        if condition is expr.condition \
                and then is expr.then \
                and else_ is expr.else_:
            return expr

        return type(expr)(condition, then, else_)

    def map_min(self,
                expr: p.Min, *args: P.args, **kwargs: P.kwargs) -> Expression:
        children = tuple([
            self.rec(child, *args, **kwargs) for child in expr.children
            ])
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(children)

    def map_max(self,
                expr: p.Max, *args: P.args, **kwargs: P.kwargs) -> Expression:
        children = tuple([
            self.rec(child, *args, **kwargs) for child in expr.children
            ])
        if all(child is orig_child
                for child, orig_child in zip(children, expr.children, strict=True)):
            return expr

        return type(expr)(children)

    def map_nan(self,
                expr: p.NaN, *args: P.args, **kwargs: P.kwargs) -> Expression:
        # Leaf node -- don't recurse
        return expr


class CachedIdentityMapper(CachedMapper[Expression, P], IdentityMapper[P]):
    pass

# }}}


# {{{ walk mapper

class WalkMapper(Mapper[None, P]):
    """A mapper whose default mapper method implementations simply recurse
    without propagating any result. Also calls :meth:`visit` for each
    visited subexpression.

    ``map_...`` methods are required to call :meth:`visit` *before*
        descending to visit their children.

    .. method:: visit(expr, *args, **kwargs)

        Returns *False* if no children of this node should be examined.

    .. method:: post_visit(expr, *args, **kwargs)

        Is called after a node's children are visited.
    """

    def map_constant(self, expr: object, *args: P.args, **kwargs: P.kwargs) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_variable(self, expr: p.Variable, *args: P.args, **kwargs: P.kwargs) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_wildcard(self, expr: p.Wildcard, *args: P.args, **kwargs: P.kwargs) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_dot_wildcard(self,
            expr: p.DotWildcard, *args: P.args, **kwargs: P.kwargs) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_star_wildcard(self,
            expr: p.StarWildcard, *args: P.args, **kwargs: P.kwargs) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_function_symbol(self,
            expr: p.FunctionSymbol, *args: P.args, **kwargs: P.kwargs) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_nan(self,
            expr: p.NaN, *args: P.args, **kwargs: P.kwargs) -> None:
        self.visit(expr, *args, **kwargs)
        self.post_visit(expr, *args, **kwargs)

    def map_call(self, expr: p.Call, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.function, *args, **kwargs)
        for child in expr.parameters:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_call_with_kwargs(self,
                expr: p.CallWithKwargs,
                *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.function, *args, **kwargs)
        for child in expr.parameters:
            self.rec(child, *args, **kwargs)

        for child in list(expr.kw_parameters.values()):
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_subscript(self,
                expr: p.Subscript,
                *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.aggregate, *args, **kwargs)
        self.rec(expr.index, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_lookup(self,
                expr: p.Lookup, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.aggregate, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_sum(self, expr: p.Sum, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_product(self, expr: p.Product, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_quotient(self, expr: p.Quotient, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.numerator, *args, **kwargs)
        self.rec(expr.denominator, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_floor_div(self,
            expr: p.FloorDiv, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.numerator, *args, **kwargs)
        self.rec(expr.denominator, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_remainder(self,
            expr: p.Remainder, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.numerator, *args, **kwargs)
        self.rec(expr.denominator, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_power(self, expr: p.Power, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.base, *args, **kwargs)
        self.rec(expr.exponent, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_tuple(self,
                expr: tuple[Expression, ...], *args: P.args, **kwargs: P.kwargs
            ) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_numpy_array(self,
            expr: np.ndarray, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        import numpy
        for i in numpy.ndindex(expr.shape):
            self.rec(expr[i], *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_multivector(self,
            expr: MultiVector[ArithmeticExpression],
            *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for _bits, coeff in expr.data.items():
            self.rec(coeff, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_common_subexpression(self,
            expr: p.CommonSubexpression, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_left_shift(self,
            expr: p.LeftShift, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.shift, *args, **kwargs)
        self.rec(expr.shiftee, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_right_shift(self,
            expr: p.RightShift, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.shift, *args, **kwargs)
        self.rec(expr.shiftee, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_bitwise_not(self,
            expr: p.BitwiseNot, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_bitwise_or(self,
                expr: p.BitwiseOr, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_bitwise_xor(self,
                expr: p.BitwiseXor, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_bitwise_and(self,
                expr: p.BitwiseAnd, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_comparison(self, expr, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.left, *args, **kwargs)
        self.rec(expr.right, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_logical_not(self,
            expr: p.LogicalNot, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_logical_or(self,
                expr: p.LogicalOr, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_logical_and(self,
                expr: p.LogicalAnd, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_if(self, expr, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.condition, *args, **kwargs)
        self.rec(expr.then, *args, **kwargs)
        self.rec(expr.else_, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_if_positive(self, expr, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.criterion, *args, **kwargs)
        self.rec(expr.then, *args, **kwargs)
        self.rec(expr.else_, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_min(self,
                expr: p.Min, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_max(self,
                expr: p.Max, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        for child in expr.children:
            self.rec(child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_substitution(self, expr, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.child, *args, **kwargs)
        for v in expr.values:
            self.rec(v, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_derivative(self, expr, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        self.rec(expr.child, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def map_slice(self, expr, *args: P.args, **kwargs: P.kwargs) -> None:
        if not self.visit(expr, *args, **kwargs):
            return

        if expr.start is not None:
            self.rec(expr.start, *args, **kwargs)
        if expr.stop is not None:
            self.rec(expr.stop, *args, **kwargs)
        if expr.step is not None:
            self.rec(expr.step, *args, **kwargs)

        self.post_visit(expr, *args, **kwargs)

    def visit(self, expr, *args: P.args, **kwargs: P.kwargs) -> bool:
        return True

    def post_visit(self, expr, *args: P.args, **kwargs: P.kwargs) -> None:
        pass


class CachedWalkMapper(CachedMapper, WalkMapper):
    pass

# }}}


# {{{ callback mapper

# FIXME: Is it worth typing this?
class CallbackMapper(Mapper):
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

    map_list = map_constant
    map_tuple = map_constant
    map_numpy_array = map_constant
    map_common_subexpression = map_constant
    map_if_positive = map_constant
    map_if = map_constant
    map_comparison = map_constant

# }}}


# {{{ caching mixins

class CSECachingMapperMixin(ABC, Generic[ResultT, P]):
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
    _cse_cache_dict: dict[tuple[Expression, P.args, P.kwargs], ResultT]

    def map_common_subexpression(self,
                expr: p.CommonSubexpression,
                *args: P.args, **kwargs: P.kwargs) -> ResultT:
        try:
            ccd = self._cse_cache_dict
        except AttributeError:
            ccd = self._cse_cache_dict = {}

        key: tuple[Expression, P.args, P.kwargs] = (
            expr, args, immutabledict(kwargs))
        try:
            return ccd[key]
        except KeyError:
            result = self.map_common_subexpression_uncached(expr, *args, **kwargs)
            ccd[key] = result
            return result

    @abstractmethod
    def map_common_subexpression_uncached(self,
                expr: p.CommonSubexpression,
                *args: P.args, **kwargs: P.kwargs) -> ResultT:
        pass

# }}}


def __getattr__(name: str) -> object:
    if name == "RecursiveMapper":
        warn("RecursiveMapper is deprecated. Use Mapper instead. "
             "RecursiveMapper will go away in 2026.",
             DeprecationWarning, stacklevel=2)
        return Mapper

    return None

# vim: foldmethod=marker
