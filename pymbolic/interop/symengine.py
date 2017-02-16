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
import symengine.sympy_compat


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

    map_Complex = map_Constant

    def map_ComplexDouble(self, expr):  # noqa
        r = self.rec(expr.real_part())
        i = self.rec(expr.imaginary_part())
        if prim.is_zero(i):
            return r
        else:
            return r + 1j * i

    map_RealDouble = SympyLikeToPymbolicMapper.to_float

    def function_name(self, expr):
        try:
            # For FunctionSymbol instances
            return expr.get_name()
        except AttributeError:
            # For builtin functions
            return type(expr).__name__

# }}}


# {{{ pymbolic -> symengine

class PymbolicToSymEngineMapper(PymbolicToSympyLikeMapper):

    sym = symengine.sympy_compat

    def raise_conversion_error(self, expr):
        raise RuntimeError(
            "do not know how to translate '%s' to symengine" % expr)

    def map_derivative(self, expr):
        return self.sym.Derivative(self.rec(expr.child),
                [self.sym.Symbol(v) for v in expr.variables])

# }}}

# vim: fdm=marker
