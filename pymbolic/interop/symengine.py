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

import symengine

import pymbolic.primitives as prim
from pymbolic.interop.common import PymbolicToSympyLikeMapper, SympyLikeToPymbolicMapper


__doc__ = """
.. class:: SymEngineToPymbolicMapper

    .. method:: __call__(expr)

.. class:: PymbolicToSymEngineMapper

    .. method:: __call__(expr)
"""


# {{{ symengine -> pymbolic

class SymEngineToPymbolicMapper(SympyLikeToPymbolicMapper):

    def map_Pow(self, expr):  # noqa
        # SymEngine likes to use as e**a to express exp(a); we undo that here.
        base, exp = expr.args
        if base == symengine.E:
            return prim.Variable("exp")(self.rec(exp))
        else:
            return prim.Power(self.rec(base), self.rec(exp))

    def map_Constant(self, expr):  # noqa
        return self.rec(expr.n())

    map_Complex = map_Constant  # noqa: N815

    def map_ComplexDouble(self, expr):  # noqa
        return complex(expr)

    map_RealDouble = SympyLikeToPymbolicMapper.to_float  # noqa: N815

    def map_Piecewise(self, expr):  # noqa
        # We only handle piecewises with 2 statements!
        if not len(expr.args) == 4:
            raise NotImplementedError
        # We only handle if/else cases
        if not (expr.args[3].is_Boolean and bool(expr.args[3]) is True):
            raise NotImplementedError
        rec_args = [self.rec(arg) for arg in expr.args[:3]]
        then, cond, else_ = rec_args
        return prim.If(cond, then, else_)

    def function_name(self, expr):
        try:
            # For FunctionSymbol instances
            return expr.get_name()
        except AttributeError:
            # For builtin functions
            return type(expr).__name__

    def not_supported(self, expr):
        from symengine.lib.symengine_wrapper import PyFunction  # pylint: disable=E0611
        if isinstance(expr, PyFunction) and \
                self.function_name(expr) == "CSE":       # pylint: disable=E0611
            sympy_expr = expr._sympy_()
            return prim.CommonSubexpression(
                self.rec(expr.args[0]), sympy_expr.prefix, sympy_expr.scope)
        elif isinstance(expr, symengine.Function) and \
                self.function_name(expr) == "CSE":
            return prim.CommonSubexpression(
                self.rec(expr.args[0]), scope=prim.cse_scope.EVALUATION)
        return SympyLikeToPymbolicMapper.not_supported(self, expr)

# }}}


# {{{ pymbolic -> symengine

class PymbolicToSymEngineMapper(PymbolicToSympyLikeMapper):

    sym = symengine

    def raise_conversion_error(self, expr):
        raise RuntimeError(f"do not know how to translate '{expr}' to symengine")


# }}}


CSE = symengine.Function("CSE")


def make_cse(arg, prefix=None, scope=None):
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
    return symengine.sympify(sympy_result)

# vim: fdm=marker
