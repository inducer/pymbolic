from __future__ import division, absolute_import

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

from pymbolic.interop.common import (
    SympyLikeToPymbolicMapper, PymbolicToSympyLikeMapper)

import pymbolic.primitives as prim
import symengine


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
        r = self.rec(expr.real_part())
        i = self.rec(expr.imaginary_part())
        if prim.is_zero(i):
            return r
        else:
            return r + 1j * i

    map_RealDouble = SympyLikeToPymbolicMapper.to_float  # noqa: N815

    def function_name(self, expr):
        try:
            # For FunctionSymbol instances
            return expr.get_name()
        except AttributeError:
            # For builtin functions
            return type(expr).__name__

    def not_supported(self, expr):  # noqa
        if isinstance(expr, symengine.Function) and \
                self.function_name(expr) == "CSE":
            return prim.CommonSubexpression(
                self.rec(expr.args[0]), expr._sympy_().prefix)
        return SympyLikeToPymbolicMapper.not_supported(self, expr)

# }}}


# {{{ pymbolic -> symengine

class PymbolicToSymEngineMapper(PymbolicToSympyLikeMapper):

    sym = symengine

    def raise_conversion_error(self, expr):
        raise RuntimeError(
            "do not know how to translate '%s' to symengine" % expr)


# }}}


def make_cse(arg, prefix=None):
    # SymEngine's classes can't be inherited, but there's a
    # mechanism to create one based on SymPy's ones which stores
    # the SymPy object inside the C++ object.
    # This SymPy object is later retrieved to get the prefix
    from pymbolic.interop.sympy import make_cse as make_cse_sympy
    sympy_result = make_cse_sympy(arg, prefix=prefix)
    return symengine.sympify(sympy_result)

# vim: fdm=marker
