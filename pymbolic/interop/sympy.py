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

import sympy

import pymbolic.primitives as prim
from pymbolic.interop.common import PymbolicToSympyLikeMapper, SympyLikeToPymbolicMapper


__doc__ = """
.. class:: SympyToPymbolicMapper

    .. method:: __call__(expr)

.. class:: PymbolicToSympyMapper

    .. method:: __call__(expr)
"""


# {{{ sympy -> pymbolic

class SympyToPymbolicMapper(SympyLikeToPymbolicMapper):

    def map_ImaginaryUnit(self, expr):  # noqa
        return 1j

    map_Float = SympyLikeToPymbolicMapper.to_float  # noqa: N815

    map_NumberSymbol = SympyLikeToPymbolicMapper.to_float  # noqa: N815

    def function_name(self, expr):
        return type(expr).__name__

    # only called for Py2
    def map_long(self, expr):
        return long(expr)  # noqa  pylint:disable=undefined-variable

    def map_Indexed(self, expr):  # noqa
        if len(expr.args) == 2:
            return prim.Subscript(
                self.rec(expr.args[0].args[0]),
                self.rec(expr.args[1]),
                )

        return prim.Subscript(
            self.rec(expr.args[0].args[0]),
            tuple([self.rec(i) for i in expr.args[1:]])
            )

    def map_CSE(self, expr):  # noqa
        return prim.CommonSubexpression(
                self.rec(expr.args[0]), expr.prefix, expr.scope)

    def map_Piecewise(self, expr):  # noqa
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

    sym = sympy

    def raise_conversion_error(self, expr):
        raise RuntimeError(f"do not know how to translate '{expr}' to sympy")

    def map_subscript(self, expr):
        return self.sym.Indexed(
            self.sym.IndexedBase(self.rec(expr.aggregate)),
            *[self.rec(i) for i in expr.index_tuple]
            )
# }}}


class CSE(sympy.Function):
    """A function to translate to a Pymbolic CSE."""
    nargs = 1


def make_cse(arg, prefix=None, scope=None):
    result = CSE(arg)
    result.prefix = prefix
    result.scope = scope
    return result


# vim: fdm=marker
