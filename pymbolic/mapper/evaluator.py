"""
.. autoclass:: EvaluationMapper
.. autoclass:: CachedEvaluationMapper
.. autoclass:: FloatEvaluationMapper
.. autoclass:: CachedFloatEvaluationMapper

.. autofunction:: evaluate
.. autofunction:: evaluate_kw
.. autofunction:: evaluate_to_float
"""

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


from pymbolic.mapper import (RecursiveMapper, CSECachingMapperMixin,
                             CachedMapper)
import operator as op
from functools import reduce


class UnknownVariableError(Exception):
    pass


class EvaluationMapper(RecursiveMapper, CSECachingMapperMixin):
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

    def __init__(self, context=None):
        """
        :arg context: a mapping from variable names to values
        """
        if context is None:
            context = {}

        self.context = context
        self.common_subexp_cache = {}

    def map_constant(self, expr):
        return expr

    def map_variable(self, expr):
        try:
            return self.context[expr.name]
        except KeyError:
            raise UnknownVariableError(expr.name)

    def map_call(self, expr):
        return self.rec(expr.function)(*[self.rec(par) for par in expr.parameters])

    def map_call_with_kwargs(self, expr):
        args = [self.rec(par) for par in expr.parameters]
        kwargs = {
                k: self.rec(v)
                for k, v in expr.kw_parameters.items()}

        return self.rec(expr.function)(*args, **kwargs)

    def map_subscript(self, expr):
        rec_result = self.rec(expr.aggregate)

        from pymbolic.primitives import Expression
        if isinstance(rec_result, Expression):
            return rec_result.index(self.rec(expr.index))
        else:
            return rec_result[self.rec(expr.index)]

    def map_lookup(self, expr):
        return getattr(self.rec(expr.aggregate), expr.name)

    def map_sum(self, expr):
        return sum(self.rec(child) for child in expr.children)

    def map_product(self, expr):
        from pytools import product
        return product(self.rec(child) for child in expr.children)

    def map_quotient(self, expr):
        return self.rec(expr.numerator) / self.rec(expr.denominator)

    def map_floor_div(self, expr):
        return self.rec(expr.numerator) // self.rec(expr.denominator)

    def map_remainder(self, expr):
        return self.rec(expr.numerator) % self.rec(expr.denominator)

    def map_power(self, expr):
        return self.rec(expr.base) ** self.rec(expr.exponent)

    def map_left_shift(self, expr):
        return self.rec(expr.shiftee) << self.rec(expr.shift)

    def map_right_shift(self, expr):
        return self.rec(expr.shiftee) >> self.rec(expr.shift)

    def map_bitwise_not(self, expr):
        # ??? Why, pylint, why ???
        # pylint: disable=invalid-unary-operand-type
        return ~self.rec(expr.child)

    def map_bitwise_or(self, expr):
        return reduce(op.or_, (self.rec(ch) for ch in expr.children))

    def map_bitwise_xor(self, expr):
        return reduce(op.xor, (self.rec(ch) for ch in expr.children))

    def map_bitwise_and(self, expr):
        return reduce(op.and_, (self.rec(ch) for ch in expr.children))

    def map_logical_not(self, expr):
        return not self.rec(expr.child)

    def map_logical_or(self, expr):
        return any(self.rec(ch) for ch in expr.children)

    def map_logical_and(self, expr):
        return all(self.rec(ch) for ch in expr.children)

    def map_polynomial(self, expr):
        # evaluate using Horner's scheme
        result = 0
        rev_data = expr.data[::-1]
        ev_base = self.rec(expr.base)

        for i, (exp, coeff) in enumerate(rev_data):
            if i+1 < len(rev_data):
                next_exp = rev_data[i+1][0]
            else:
                next_exp = 0
            result = (result+coeff)*ev_base**(exp-next_exp)

        return result

    def map_list(self, expr):
        return [self.rec(child) for child in expr]

    def map_numpy_array(self, expr):
        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        for i in numpy.ndindex(expr.shape):
            result[i] = self.rec(expr[i])
        return result

    def map_multivector(self, expr, *args):
        return expr.map(lambda ch: self.rec(ch, *args))

    def map_common_subexpression_uncached(self, expr):
        return self.rec(expr.child)

    def map_if_positive(self, expr):
        if self.rec(expr.criterion) > 0:
            return self.rec(expr.then)
        else:
            return self.rec(expr.else_)

    def map_comparison(self, expr):
        import operator
        return getattr(operator, expr.operator_to_name[expr.operator])(
            self.rec(expr.left), self.rec(expr.right))

    def map_if(self, expr):
        if self.rec(expr.condition):
            return self.rec(expr.then)
        else:
            return self.rec(expr.else_)

    def map_min(self, expr):
        return min(self.rec(child) for child in expr.children)

    def map_max(self, expr):
        return max(self.rec(child) for child in expr.children)

    def map_tuple(self, expr):
        return tuple([self.rec(child) for child in expr])

    def map_nan(self, expr):
        if expr.data_type is None:
            from math import nan
            return nan
        else:
            return expr.data_type(float("nan"))


class CachedEvaluationMapper(CachedMapper, EvaluationMapper):
    def __init__(self, context=None):
        CachedMapper.__init__(self)
        EvaluationMapper.__init__(self, context=context)


class FloatEvaluationMapper(EvaluationMapper):
    def map_constant(self, expr):
        return float(expr)

    def map_rational(self, expr):
        return self.rec(expr.numerator) / self.rec(expr.denominator)


class CachedFloatEvaluationMapper(CachedEvaluationMapper):
    def map_constant(self, expr):
        return float(expr)

    def map_rational(self, expr):
        return self.rec(expr.numerator) / self.rec(expr.denominator)


def evaluate(expression, context=None, mapper_cls=CachedEvaluationMapper):
    """
    :arg mapper_cls: A :class:`type` of the evaluation mapper
        whose instance performs the evaluation.
    """
    if context is None:
        context = {}
    return mapper_cls(context)(expression)


def evaluate_kw(expression, mapper_cls=CachedEvaluationMapper, **context):
    """
    :arg mapper_cls: A :class:`type` of the evaluation mapper
        whose instance performs the evaluation.
    """
    return mapper_cls(context)(expression)


def evaluate_to_float(expression, context=None,
                      mapper_cls=CachedFloatEvaluationMapper):
    """
    :arg mapper_cls: A :class:`type` of the evaluation mapper
        whose instance performs the evaluation.
    """
    if context is None:
        context = {}
    return mapper_cls(context)(expression)
