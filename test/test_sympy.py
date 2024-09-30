from __future__ import annotations


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


x_, y_, i_, j_ = (prim.Variable(s) for s in "x y i j".split())


# {{{ to pymbolic test

def _test_to_pymbolic(mapper, sym, use_symengine):
    x, y = sym.symbols("x,y")

    assert mapper(sym.Rational(3, 4)) == prim.Quotient(3, 4)
    assert mapper(sym.Integer(6)) == 6

    if not use_symengine:
        assert mapper(sym.Subs(x**2, (x,), (y,))) == \
            prim.Substitution(x_**2, ("x",), (y_,))
        deriv = sym.Derivative(x**2, x)
        assert mapper(deriv) == prim.Derivative(x_**2, ("x",))
    else:
        assert mapper(sym.Subs(x**2, (x,), (y,))) == \
            y_**2
        deriv = sym.Derivative(x**2, x)
        assert mapper(deriv) == 2*x_

    # functions
    assert mapper(sym.Function("f")(x)) == prim.Variable("f")(x_)
    assert mapper(sym.exp(x)) == prim.Variable("exp")(x_)

    # indexed accesses
    i, j = sym.symbols("i,j")
    if not use_symengine:
        idx = sym.Indexed(x, i, j)
    else:
        idx = sym.Function("Indexed")(x, i, j)
    assert mapper(idx) == x_[i_, j_]

    # constants
    import math
    # FIXME: Why isn't this exact?
    assert abs(mapper(sym.pi) - math.pi) < 1e-14
    assert abs(mapper(sym.E) - math.e) < 1e-14
    assert mapper(sym.I) == 1j

# }}}


def test_symengine_to_pymbolic():
    sym = pytest.importorskip("symengine")
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
    deriv = sym.Derivative(x**2, x)
    assert mapper(prim.Derivative(x_**2, ("x",))) == deriv
    floordiv = sym.floor(x / y)
    assert mapper(prim.FloorDiv(x_, y_)) == floordiv

    if use_symengine:
        assert mapper(x_[0]) == sym.Function("Indexed")("x", 0)
    else:
        i, j = sym.symbols("i,j")
        assert mapper(x_[i_, j_]) == sym.Indexed(x, i, j)

    assert mapper(prim.Variable("f")(x_)) == sym.Function("f")(x)

# }}}


def test_pymbolic_to_symengine():
    sym = pytest.importorskip("symengine")
    from pymbolic.interop.symengine import PymbolicToSymEngineMapper
    mapper = PymbolicToSymEngineMapper()

    _test_from_pymbolic(mapper, sym, True)


def test_pymbolic_to_sympy():
    sym = pytest.importorskip("sympy")
    from pymbolic.interop.sympy import PymbolicToSympyMapper
    mapper = PymbolicToSympyMapper()

    _test_from_pymbolic(mapper, sym, False)


# {{{ roundtrip tests

def _test_roundtrip(forward, backward, sym, use_symengine):
    exprs = [
        2 + x_,
        2 * x_,
        x_ ** 2,
        x_[0],
        x_[i_, j_],
        prim.Variable("f")(x_),
        prim.If(prim.Comparison(x_, "<=", y_), 1, 0),
    ]

    for expr in exprs:
        assert expr == backward(forward(expr))

# }}}


def test_pymbolic_to_sympy_roundtrip():
    sym = pytest.importorskip("sympy")
    from pymbolic.interop.sympy import PymbolicToSympyMapper, SympyToPymbolicMapper
    forward = PymbolicToSympyMapper()
    backward = SympyToPymbolicMapper()

    _test_roundtrip(forward, backward, sym, False)


def test_pymbolic_to_symengine_roundtrip():
    sym = pytest.importorskip("symengine")
    from pymbolic.interop.symengine import (
        PymbolicToSymEngineMapper,
        SymEngineToPymbolicMapper,
    )
    forward = PymbolicToSymEngineMapper()
    backward = SymEngineToPymbolicMapper()

    _test_roundtrip(forward, backward, sym, True)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from pytest import main
        main([__file__])
