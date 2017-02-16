from __future__ import division

__copyright__ = "Copyright (C) 2017 Matt Wala"

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

import pytest
import pymbolic.primitives as prim

x_, y_ = (prim.Variable(s) for s in "x y".split())


# {{{ to pymbolic test

def _test_to_pymbolic(mapper, sym, use_symengine):
    x, y = sym.symbols("x,y")

    assert mapper(sym.Rational(3, 4)) == prim.Quotient(3, 4)
    assert mapper(sym.Integer(6)) == 6

    assert mapper(sym.Subs(x**2, (x,), (y,))) == \
        prim.Substitution(x_**2, ("x",), (y_,))
    # FIXME in symengine
    deriv = sym.Derivative(x**2, (x,)) if use_symengine else sym.Derivative(x**2, x)
    assert mapper(deriv) == prim.Derivative(x_**2, ("x",))

    # functions
    assert mapper(sym.Function("f")(x)) == prim.Variable("f")(x_)
    assert mapper(sym.exp(x)) == prim.Variable("exp")(x_)

    # constants
    import math
    # FIXME: Why isn't this exact?
    assert abs(mapper(sym.pi) - math.pi) < 1e-14
    assert abs(mapper(sym.E) - math.e) < 1e-14
    assert mapper(sym.I) == 1j

# }}}


def test_symengine_to_pymbolic():
    sym = pytest.importorskip("symengine.sympy_compat")
    from pymbolic.interop.symengine import SymEngineToPymbolicMapper
    mapper = SymEngineToPymbolicMapper()

    _test_to_pymbolic(mapper, sym, True)


def test_sympy_to_pymbolic():
    sym = pytest.importorskip("sympy")
    from pymbolic.interop.sympy import SympyToPymbolicMapper
    mapper = SympyToPymbolicMapper()

    _test_to_pymbolic(mapper, sym, False)


# {{{ from pymbolic test

def _test_from_pymbolic(mapper, sym, use_symengine):
    x, y = sym.symbols("x,y")

    assert mapper(x_ + y_) == x + y
    assert mapper(x_ * y_) == x * y
    assert mapper(x_ ** 2) == x ** 2

    assert mapper(prim.Substitution(x_**2, ("x",), (y_,))) == \
        sym.Subs(x**2, (x,), (y,))
    # FIXME in symengine
    deriv = sym.Derivative(x**2, (x,)) if use_symengine else sym.Derivative(x**2, x)
    assert mapper(prim.Derivative(x_**2, ("x",))) == deriv

    assert mapper(x_[0]) == sym.Symbol("x_0")

    assert mapper(prim.Variable("f")(x_)) == sym.Function("f")(x)

# }}}


def test_pymbolic_to_symengine():
    sym = pytest.importorskip("symengine.sympy_compat")
    from pymbolic.interop.symengine import PymbolicToSymEngineMapper
    mapper = PymbolicToSymEngineMapper()

    _test_from_pymbolic(mapper, sym, True)


def test_pymbolic_to_sympy():
    sym = pytest.importorskip("sympy")
    from pymbolic.interop.sympy import PymbolicToSympyMapper
    mapper = PymbolicToSympyMapper()

    _test_from_pymbolic(mapper, sym, False)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
