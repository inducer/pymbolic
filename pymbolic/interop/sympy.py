from __future__ import annotations


__copyright__ = """
Copyright (C) 2017 Matt Wala
Copyright (C) 2009-2013 Andreas Kloeckner
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

import sympy as sp
from typing_extensions import override

import pymbolic.primitives as prim
from pymbolic.interop.common import (
    PymbolicToSympyLikeMapper,
    SympyLikeExpression,
    SympyLikeToPymbolicMapper,
)


if TYPE_CHECKING:
    from sympy.core.numbers import ImaginaryUnit

    from pymbolic.typing import Expression

__doc__ = """
.. class:: SympyToPymbolicMapper

    .. method:: __call__(expr)

.. class:: PymbolicToSympyMapper

    .. method:: __call__(expr)
"""


# {{{ sympy -> pymbolic

class SympyToPymbolicMapper(SympyLikeToPymbolicMapper):
    @override
    def function_name(self, expr: object) -> str:
        return type(expr).__name__

    def map_ImaginaryUnit(self, expr: ImaginaryUnit) -> Expression:
        return 1j

    def map_Float(self, expr: sp.Float) -> Expression:
        return self.to_float(expr)

    def map_NumberSymbol(self, expr: sp.NumberSymbol) -> Expression:
        return self.to_float(expr)

    def map_Indexed(self, expr: sp.Indexed) -> Expression:
        if len(expr.args) == 2:
            return prim.Subscript(
                self.rec(expr.args[0].args[0]),
                self.rec(expr.args[1]),
                )

        return prim.Subscript(
            self.rec(expr.args[0].args[0]),
            tuple([self.rec(i) for i in expr.args[1:]])
            )

    def map_CSE(self, expr: CSE) -> Expression:
        return prim.CommonSubexpression(
                self.rec(expr.args[0]), expr.prefix, expr.scope)

    def map_Piecewise(self, expr: sp.Piecewise) -> Expression:
        # We only handle piecewises with 2 arguments!
        if not len(expr.args) == 2:
            raise NotImplementedError

        # We only handle if/else cases
        if not (expr.args[1][1].is_Boolean and bool(expr.args[1][1]) is True):
            raise NotImplementedError

        then = self.rec(expr.args[0][0])
        else_ = self.rec(expr.args[1][0])
        cond = self.rec(expr.args[0][1])
        return prim.If(cond, then, else_)

# }}}


# {{{ pymbolic -> sympy

class PymbolicToSympyMapper(PymbolicToSympyLikeMapper):
    @property
    @override
    def sym(self) -> Any:
        return sp

    @override
    def raise_conversion_error(self, expr: object) -> None:
        raise RuntimeError(f"do not know how to translate '{expr}' to sympy")

    @override
    def map_subscript(self, expr: prim.Subscript) -> SympyLikeExpression:
        return self.sym.Indexed(
            self.sym.IndexedBase(self.rec(expr.aggregate)),
            *[self.rec(i) for i in expr.index_tuple]
            )
# }}}


class CSE(sp.Function):
    """
    A function to translate to a :class:`~pymbolic.primitives.CommonSubexpression`.
    """

    nargs: int = 1


def make_cse(arg: SympyLikeExpression,
             prefix: str | None = None,
             scope: str | None = None) -> CSE:
    result = CSE(arg)

    # FIXME: make these parts of the CSE class properly?
    result.prefix = prefix  # pyright: ignore[reportAttributeAccessIssue]
    result.scope = scope  # pyright: ignore[reportAttributeAccessIssue]

    return result  # pyright: ignore[reportReturnType]


# vim: fdm=marker
