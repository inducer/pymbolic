from __future__ import annotations


__copyright__ = """
Copyright (C) 2017 Matt Wala
"""

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

from typing import TYPE_CHECKING, Any

import symengine as sp
from typing_extensions import override

import pymbolic.primitives as prim
from pymbolic.interop.common import (
    PymbolicToSympyLikeMapper,
    SympyLikeExpression,
    SympyLikeToPymbolicMapper,
)


if TYPE_CHECKING:
    import optype

    from pymbolic.typing import Expression

__doc__ = """
.. autoclass:: SymEngineToPymbolicMapper
.. autoclass:: PymbolicToSymEngineMapper
"""


# {{{ symengine -> pymbolic

class SymEngineToPymbolicMapper(SympyLikeToPymbolicMapper):
    """
    .. automethod:: __call__
    """

    def map_Pow(self, expr: sp.Pow) -> Expression:
        # SymEngine likes to use as e**a to express exp(a); we undo that here.
        base, exp = expr.args
        if base == sp.E:
            return prim.Variable("exp")(self.rec(exp))
        else:
            return prim.Power(self.rec(base), self.rec(exp))

    def map_Constant(self, expr: object) -> Expression:
        return self.rec(expr.n())

    def map_Complex(self, expr: object) -> Expression:
        return self.rec(expr.n())

    def map_ComplexDouble(self, expr: optype.CanComplex) -> Expression:
        return complex(expr)

    def map_RealDouble(self, expr: optype.CanFloat) -> Expression:
        return self.to_float(expr)

    def map_Piecewise(self, expr: sp.Piecewise) -> Expression:
        # We only handle piecewises with 2 statements!
        if not len(expr.args) == 4:
            raise NotImplementedError

        # We only handle if/else cases
        if not (expr.args[3].is_Boolean and bool(expr.args[3]) is True):
            raise NotImplementedError

        rec_args = [self.rec(arg) for arg in expr.args[:3]]
        then, cond, else_ = rec_args
        return prim.If(cond, then, else_)

    @override
    def function_name(self, expr: object) -> str:
        try:
            # For FunctionSymbol instances
            return expr.get_name()
        except AttributeError:
            # For builtin functions
            return type(expr).__name__

    @override
    def not_supported(self, expr: object) -> Expression:
        from symengine.lib.symengine_wrapper import PyFunction

        if isinstance(expr, PyFunction) and self.function_name(expr) == "CSE":
            sympy_expr = expr._sympy_()
            return prim.CommonSubexpression(
                self.rec(expr.args[0]), sympy_expr.prefix, sympy_expr.scope)
        elif isinstance(expr, sp.Function) and self.function_name(expr) == "CSE":
            return prim.CommonSubexpression(
                self.rec(expr.args[0]), scope=prim.cse_scope.EVALUATION)
        return SympyLikeToPymbolicMapper.not_supported(self, expr)

# }}}


# {{{ pymbolic -> symengine

class PymbolicToSymEngineMapper(PymbolicToSympyLikeMapper):
    """
    .. automethod:: __call__
    """

    @property
    @override
    def sym(self) -> Any:
        return sp

    def to_expr(self, expr: Expression) -> sp.Expr:
        # Don't be tempted to insert type-asserts here. Symengine's class hierarchy
        # does not agree with sympy, for example a Symbol is not an Expr in symengine.
        return self(expr)

    @override
    def raise_conversion_error(self, expr: object) -> None:
        raise RuntimeError(f"do not know how to translate '{expr}' to symengine")


# }}}


CSE = sp.Function("CSE")


def make_cse(arg: SympyLikeExpression,
             prefix: str | None = None,
             scope: str | None = None) -> sp.Function:
    # SymEngine's classes can't be inherited, but there's a
    # mechanism to create one based on SymPy's ones which stores
    # the SymPy object inside the C++ object.
    # This SymPy object is later retrieved to get the prefix
    # These conversions between SymPy and SymEngine are expensive,
    # so use it only if necessary.
    if prefix is None and scope is None:
        return CSE(arg)

    from pymbolic.interop.sympy import make_cse as make_cse_sympy
    sympy_result = make_cse_sympy(arg, prefix=prefix, scope=scope)

    return sp.sympify(sympy_result)

# vim: fdm=marker
