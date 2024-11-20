"""
.. autoclass:: EvaluationMapper
.. autoclass:: CachedEvaluationMapper
.. autoclass:: FloatEvaluationMapper
.. autoclass:: CachedFloatEvaluationMapper

.. autofunction:: evaluate
.. autofunction:: evaluate_kw
.. autofunction:: evaluate_to_float
"""
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

import operator as op
from collections.abc import Mapping
from functools import reduce
from typing import TYPE_CHECKING, cast

import pymbolic.primitives as p
from pymbolic.mapper import CachedMapper, CSECachingMapperMixin, Mapper, ResultT
from pymbolic.typing import Expression


if TYPE_CHECKING:
    import numpy as np

    from pymbolic.geometric_algebra import MultiVector


class UnknownVariableError(Exception):
    pass


class EvaluationMapper(Mapper[ResultT, []], CSECachingMapperMixin):
    """Example usage:

    .. doctest::

        >>> import pymbolic.primitives as p
        >>> x = p.Variable("x")

        >>> u = 5*x**2 - 3*x
        >>> print(u)
        5*x**2 + (-1)*3*x

        >>> from pymbolic.mapper.evaluator import EvaluationMapper as EM
        >>> EM(context={"x": 5})(u)
        110
    """

    context: Mapping[str, ResultT]

    def __init__(self, context: Mapping[str, ResultT] | None = None) -> None:
        """
        :arg context: a mapping from variable names to values
        """
        if context is None:
            context = {}

        self.context = context

    def map_constant(self, expr: object) -> ResultT:
        return cast(ResultT, expr)

    def map_variable(self, expr: p.Variable) -> ResultT:
        try:
            return self.context[expr.name]
        except KeyError:
            raise UnknownVariableError(expr.name) from None

    def map_call(self, expr: p.Call) -> ResultT:
        return self.rec(expr.function)(*[self.rec(par) for par in expr.parameters])  # type: ignore[operator]

    def map_call_with_kwargs(self, expr: p.CallWithKwargs) -> ResultT:
        args = [self.rec(par) for par in expr.parameters]
        kwargs = {
                k: self.rec(v)
                for k, v in expr.kw_parameters.items()}

        return self.rec(expr.function)(*args, **kwargs)  # type: ignore[operator]

    def map_subscript(self, expr: p.Subscript) -> ResultT:
        return self.rec(expr.aggregate)[self.rec(expr.index)]  # type: ignore[index]

    def map_lookup(self, expr: p.Lookup) -> ResultT:
        return getattr(self.rec(expr.aggregate), expr.name)

    def map_sum(self, expr: p.Sum) -> ResultT:
        return sum(self.rec(child) for child in expr.children)  # type: ignore[return-value, misc]

    def map_product(self, expr: p.Product) -> ResultT:
        from pytools import product
        return product(self.rec(child) for child in expr.children)

    def map_quotient(self, expr: p.Quotient) -> ResultT:
        return self.rec(expr.numerator) / self.rec(expr.denominator)  # type: ignore[operator]

    def map_floor_div(self, expr: p.FloorDiv) -> ResultT:
        return self.rec(expr.numerator) // self.rec(expr.denominator)  # type: ignore[operator]

    def map_remainder(self, expr: p.Remainder) -> ResultT:
        return self.rec(expr.numerator) % self.rec(expr.denominator)  # type: ignore[operator]

    def map_power(self, expr: p.Power) -> ResultT:
        return self.rec(expr.base) ** self.rec(expr.exponent)  # type: ignore[operator]

    def map_left_shift(self, expr: p.LeftShift) -> ResultT:
        return self.rec(expr.shiftee) << self.rec(expr.shift)  # type: ignore[operator]

    def map_right_shift(self, expr: p.RightShift) -> ResultT:
        return self.rec(expr.shiftee) >> self.rec(expr.shift)  # type: ignore[operator]

    def map_bitwise_not(self, expr: p.BitwiseNot) -> ResultT:
        # ??? Why, pylint, why ???
        # pylint: disable=invalid-unary-operand-type
        return ~self.rec(expr.child)  # type: ignore[operator]

    def map_bitwise_or(self, expr: p.BitwiseOr) -> ResultT:
        return reduce(op.or_, (self.rec(ch) for ch in expr.children))

    def map_bitwise_xor(self, expr: p.BitwiseXor) -> ResultT:
        return reduce(op.xor, (self.rec(ch) for ch in expr.children))

    def map_bitwise_and(self, expr: p.BitwiseAnd) -> ResultT:
        return reduce(op.and_, (self.rec(ch) for ch in expr.children))

    def map_logical_not(self, expr: p.LogicalNot) -> bool:  # type: ignore[override]
        return not self.rec(expr.child)

    def map_logical_or(self, expr: p.LogicalOr) -> bool:  # type: ignore[override]
        return any(self.rec(ch) for ch in expr.children)

    def map_logical_and(self, expr: p.LogicalAnd) -> bool:  # type: ignore[override]
        return all(self.rec(ch) for ch in expr.children)

    def map_list(self, expr: list[Expression]) -> ResultT:
        return [self.rec(child) for child in expr]  # type: ignore[return-value]

    def map_numpy_array(self, expr: np.ndarray) -> ResultT:
        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        for i in numpy.ndindex(expr.shape):
            result[i] = self.rec(expr[i])
        return result  # type: ignore[return-value]

    def map_multivector(self, expr: MultiVector) -> ResultT:
        return expr.map(lambda ch: self.rec(ch))  # type: ignore[return-value]

    def map_common_subexpression_uncached(self, expr: p.CommonSubexpression) -> ResultT:
        return self.rec(expr.child)

    def map_if(self, expr: p.If) -> ResultT:
        if self.rec(expr.condition):
            return self.rec(expr.then)
        else:
            return self.rec(expr.else_)

    def map_comparison(self, expr: p.Comparison) -> ResultT:
        import operator
        return getattr(operator, expr.operator_to_name[expr.operator])(
            self.rec(expr.left), self.rec(expr.right))

    def map_min(self, expr: p.Min) -> ResultT:
        return min(self.rec(child) for child in expr.children)  # type: ignore[type-var]

    def map_max(self, expr: p.Max) -> ResultT:
        return max(self.rec(child) for child in expr.children)  # type: ignore[type-var]

    def map_tuple(self, expr: tuple[Expression, ...]) -> ResultT:
        return tuple([self.rec(child) for child in expr])  # type: ignore[return-value]

    def map_nan(self, expr: p.NaN) -> ResultT:
        if expr.data_type is None:
            from math import nan
            return nan  # type:ignore[return-value]
        else:
            return expr.data_type(float("nan"))


class CachedEvaluationMapper(CachedMapper[ResultT, []], EvaluationMapper[ResultT]):
    def __init__(self, context=None):
        CachedMapper.__init__(self)
        EvaluationMapper.__init__(self, context=context)


class FloatEvaluationMapper(EvaluationMapper[float]):
    def map_constant(self, expr) -> float:
        return float(expr)

    def map_rational(self, expr) -> float:
        return self.rec(expr.numerator) / self.rec(expr.denominator)


class CachedFloatEvaluationMapper(CachedEvaluationMapper[float]):
    def map_constant(self, expr) -> float:
        return float(expr)

    def map_rational(self, expr) -> float:
        return self.rec(expr.numerator) / self.rec(expr.denominator)


def evaluate(
            expression: Expression,
            context: Mapping[str, ResultT] | None = None,
            mapper_cls: type[EvaluationMapper[ResultT]] = CachedEvaluationMapper,
        ) -> ResultT:
    """
    :arg mapper_cls: A :class:`type` of the evaluation mapper
        whose instance performs the evaluation.
    """
    if context is None:
        context = {}
    return mapper_cls(context)(expression)


def evaluate_kw(
            expression: Expression,
            mapper_cls: type[EvaluationMapper[ResultT]] = CachedEvaluationMapper,
            **context: ResultT,
        ) -> ResultT:
    """
    :arg mapper_cls: A :class:`type` of the evaluation mapper
        whose instance performs the evaluation.
    """
    return mapper_cls(context)(expression)


def evaluate_to_float(expression, context=None,
                      mapper_cls=CachedFloatEvaluationMapper) -> float:
    """
    :arg mapper_cls: A :class:`type` of the evaluation mapper
        whose instance performs the evaluation.
    """
    if context is None:
        context = {}
    return mapper_cls(context)(expression)
