"""
.. autoclass:: FunctionDerivativeTaker
.. autoclass:: DifferentiationMapper
    :show-inheritance:
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

from typing import TYPE_CHECKING, Any, Concatenate, Literal, Protocol

from typing_extensions import Self, override

import pymbolic.primitives as prim
from pymbolic.mapper import CSECachingMapperMixin, Mapper, P
from pymbolic.typing import ArithmeticExpression, Expression


if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from numpy.typing import NDArray

Smoothness = Literal["none", "continuous", "discontinuous"]


class FunctionDerivativeTaker(Protocol):
    """Inherits: :class:`typing.Protocol`.

    .. automethod:: __call__
    """

    def __call__(self,
            i: int,
            func: Expression,
            pars: Sequence[Expression],
            allowed_nonsmoothness: (
                 Literal["none", "continuous", "discontinuous"]) = "none",
        ) -> ArithmeticExpression: ...


def map_math_functions_by_name(
            i: int,
            func: Expression,
            pars: Sequence[Expression],
            allowed_nonsmoothness: Smoothness = "none",
        ) -> ArithmeticExpression:
    def make_f(name: str) -> prim.ExpressionNode:
        return prim.Lookup(prim.Variable("math"), name)

    if func == make_f("sin") and len(pars) == 1:
        assert i == 0
        return make_f("cos")(*pars)
    elif func == make_f("cos") and len(pars) == 1:
        assert i == 0
        return -make_f("sin")(*pars)
    elif func == make_f("tan") and len(pars) == 1:
        assert i == 0
        return make_f("tan")(*pars)**2+1
    elif func == make_f("log") and len(pars) == 1:
        assert i == 0
        assert prim.is_arithmetic_expression(pars[0])
        return prim.quotient(1, pars[0])
    elif func == make_f("exp") and len(pars) == 1:
        assert i == 0
        return make_f("exp")(*pars)
    elif func == make_f("sinh") and len(pars) == 1:
        assert i == 0
        return make_f("cosh")(*pars)
    elif func == make_f("cosh") and len(pars) == 1:
        assert i == 0
        return make_f("sinh")(*pars)
    elif func == make_f("tanh") and len(pars) == 1:
        assert i == 0
        return 1-make_f("tanh")(*pars)**2
    elif func == make_f("expm1") and len(pars) == 1:
        assert i == 0
        return make_f("exp")(*pars)
    elif func == make_f("fabs") and len(pars) == 1:
        assert i == 0

        par, = pars
        assert prim.is_arithmetic_expression(par)

        if allowed_nonsmoothness in ["continuous", "discontinuous"]:
            from pymbolic.functions import sign
            return sign(par)
        else:
            raise ValueError(
                "'fabs' is not smooth, pass allowed_nonsmoothness='continuous' "
                "to return 'sign' function")
    elif func == make_f("copysign") and len(pars) == 2:
        # NOTE: this is the `sign(x) = copysign(1, x)` function actually, as
        # defined in `pymbolic.functions`, so even though it has 2 arguments, we
        # only look at derivatives with respect to the second one.
        if allowed_nonsmoothness == "discontinuous":
            return 0
        else:
            raise ValueError(
                "'sign' is discontinuous, pass allowed_nonsmoothness='discontinuous' "
                "to return 0")
    else:
        raise RuntimeError("unrecognized function, cannot differentiate")


class DifferentiationMapper(Mapper[Expression, P],
                            CSECachingMapperMixin[Expression, P]):
    """Example usage:

    .. doctest::
        :options: +NORMALIZE_WHITESPACE

        >>> import pymbolic.primitives as p
        >>> x = p.Variable("x")
        >>> expr = x*(x+5)**3/(x-1)**2

        >>> from pymbolic import flatten
        >>> from pymbolic.mapper.differentiator import DifferentiationMapper as DM
        >>> print(flatten(DM(x)(expr)))
        (((x + 5)**3 + x*3*(x + 5)**2)*(x + -1)**2 + (-1)*2*(x + -1)*x*(x + 5)**3) / (x + -1)**2**2
    """  # noqa: E501

    variable: prim.Variable | prim.Subscript
    function_map: FunctionDerivativeTaker
    allowed_nonsmoothness: Smoothness

    def __init__(self,
                 variable: prim.Variable | prim.Subscript,
                 func_map: FunctionDerivativeTaker | None = None,
                 allowed_nonsmoothness: Smoothness | None = None) -> None:
        """
        :arg variable: A :class:`pymbolic.primitives.Variable` instance
            by which to differentiate.
        :arg func_map: A function for computing derivatives of function
            calls, signature ``(arg_index, function_variable, parameters)``.
        :arg allowed_nonsmoothness: Whether to allow differentiation of
            functions which are not smooth or continuous.
            Pass ``"continuous"`` to allow nonsmooth but not discontinuous
            functions or ``"discontinuous"`` to allow both.
            Defaults to ``"none"``, in which case neither is allowed.

        .. versionchanged:: 2019.2

            Added *allowed_nonsmoothness*.
        """

        if func_map is None:
            func_map = map_math_functions_by_name

        if allowed_nonsmoothness is None:
            allowed_nonsmoothness = "none"

        self.variable = variable
        self.function_map = func_map
        if allowed_nonsmoothness not in ["none", "continuous", "discontinuous"]:
            raise ValueError(f"allowed_nonsmoothness={allowed_nonsmoothness} "
                    "is not a valid option")
        self.allowed_nonsmoothness = allowed_nonsmoothness

    def rec_arith(self, expr: Expression, /,
                  *args: P.args, **kwargs: P.kwargs) -> ArithmeticExpression:
        result = self.rec(expr, *args, **kwargs)
        assert prim.is_arithmetic_expression(result)

        return result

    def rec_undiff(self, expr: ArithmeticExpression, /,
                   *args: P.args, **kwargs: P.kwargs) -> ArithmeticExpression:
        """This method exists for the benefit of subclasses that may need to
        process un-differentiated subexpressions.
        """
        return expr

    @override
    def map_constant(self, expr: object, /,
                     *args: P.args, **kwargs: P.kwargs) -> Expression:
        return 0

    @override
    def map_variable(self, expr: prim.Variable | prim.Subscript, /,
                     *args: P.args, **kwargs: P.kwargs) -> Expression:
        if expr == self.variable:
            return 1
        else:
            return 0

    @override
    def map_call(self, expr: prim.Call, /,
                 *args: P.args, **kwargs: P.kwargs) -> Expression:
        pars = tuple(self.rec_undiff(p, *args, **kwargs) for p in expr.parameters)
        return prim.flattened_sum(
            self.function_map(
                i,
                expr.function,
                pars,
                allowed_nonsmoothness=self.allowed_nonsmoothness)
            * self.rec_arith(param, *args, **kwargs)
            for i, param in enumerate(expr.parameters)
            )

    map_subscript: Callable[Concatenate[Self, prim.Subscript, P],
                            Expression] = map_variable

    @override
    def map_sum(self, expr: prim.Sum, /, *
                args: P.args, **kwargs: P.kwargs) -> Expression:
        return prim.flattened_sum(
                self.rec_arith(child, *args, **kwargs) for child in expr.children)

    @override
    def map_product(self, expr: prim.Product, /,
                    *args: P.args, **kwargs: P.kwargs) -> Expression:
        return prim.flattened_sum(
            prim.flattened_product(
                [self.rec_undiff(ch, *args, **kwargs) for ch in expr.children[0:i]]
                + [self.rec_arith(child, *args, **kwargs)]
                + [self.rec_undiff(ch, *args, **kwargs) for ch in expr.children[i+1:]]
                )
            for i, child in enumerate(expr.children))

    @override
    def map_quotient(self, expr: prim.Quotient, /,
                     *args: P.args, **kwargs: P.kwargs) -> Expression:
        f = expr.numerator
        g = expr.denominator
        df = self.rec_arith(f, *args, **kwargs)
        dg = self.rec_arith(g, *args, **kwargs)
        f = self.rec_undiff(f, *args, **kwargs)
        g = self.rec_undiff(g, *args, **kwargs)

        if (not df) and (not dg):
            return 0
        elif (not df):
            return -f*dg/g**2
        elif (not dg):
            return self.rec_arith(f, *args, **kwargs) / g
        else:
            return (df*g-dg*f)/g**2

    @override
    def map_power(self, expr: prim.Power, /,
                  *args: P.args, **kwargs: P.kwargs) -> Expression:
        f = expr.base
        g = expr.exponent
        df = self.rec_arith(f, *args, **kwargs)
        dg = self.rec_arith(g, *args, **kwargs)
        f = self.rec_undiff(f, *args, **kwargs)
        g = self.rec_undiff(g, *args, **kwargs)

        log = prim.Variable("log")

        if not df and not dg:
            return 0
        elif not df:
            return log(f) * f**g * dg
        elif not dg:
            return g * f**(g-1) * df
        else:
            return log(f) * f**g * dg + g * f**(g-1) * df

    @override
    def map_numpy_array(self, expr: NDArray[Any], /,
                        *args: P.args, **kwargs: P.kwargs) -> Expression:
        import numpy as np
        result = np.empty(expr.shape, dtype=object)

        from pytools import ndindex
        for i in ndindex(result.shape):
            result[i] = self.rec(expr[i], *args, **kwargs)

        return result

    @override
    def map_if(self, expr: prim.If, /,
               *args: P.args, **kwargs: P.kwargs) -> Expression:
        if self.allowed_nonsmoothness != "discontinuous":
            raise ValueError(
                    "cannot differentiate 'If' nodes unless allowed_nonsmoothness "
                    f"is set to 'discontinuous': {self.allowed_nonsmoothness!r}")

        return type(expr)(
                expr.condition,
                self.rec(expr.then, *args, **kwargs),
                self.rec(expr.else_, *args, **kwargs))

    @override
    def map_common_subexpression_uncached(
                self, expr: prim.CommonSubexpression, /,
                *args: P.args, **kwargs: P.kwargs) -> Expression:
        return type(expr)(
                self.rec(expr.child, *args, **kwargs),
                expr.prefix,
                expr.scope)


def differentiate(expression: Expression,
                  variable: str | prim.Variable | prim.Subscript,
                  func_mapper: FunctionDerivativeTaker | None = None,
                  allowed_nonsmoothness: Smoothness = "none") -> Expression:
    if not isinstance(variable, prim.Variable | prim.Subscript):
        variable = prim.make_variable(variable)

    from pymbolic import flatten

    return flatten(DifferentiationMapper(
            variable,
            func_map=func_mapper,
            allowed_nonsmoothness=allowed_nonsmoothness
        )(expression))
