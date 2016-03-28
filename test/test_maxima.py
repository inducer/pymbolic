from __future__ import division

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

import pytest
from pytools.test import mark_test

from pymbolic.interop.maxima import MaximaKernel


def test_kernel():
    pytest.importorskip("pexpect")

    knl = MaximaKernel()
    knl.exec_str("k:1/(sqrt((x0-(a+t*b))^2+(y0-(c+t*d))^2+(z0-(e+t*f))^2))")
    knl.eval_str("sum(diff(k, t,deg)*t^deg,deg,0,6)")
    assert knl.eval_str("2+2").strip() == "4"
    knl.shutdown()


def pytest_funcarg__knl(request):
    pytest.importorskip("pexpect")

    knl = MaximaKernel()
    request.addfinalizer(knl.shutdown)
    return knl


def test_setup(knl):
    pytest.importorskip("pexpect")

    knl.clean_eval_str_with_setup(
            ["k:1/(sqrt((x0-(a+t*b))^2+(y0-(c+t*d))^2+(z0-(e+t*f))^2))"],
            "sum(diff(k, t,deg)*t^deg,deg,0,6)")


def test_error(knl):
    from pymbolic.interop.maxima import MaximaError
    try:
        knl.eval_str("))(!")
    except MaximaError:
        pass

    try:
        knl.eval_str("integrate(1/(x^3*(a+b*x)^(1/3)),x)")
    except MaximaError:
        pass


def test_strict_round_trip(knl):
    from pymbolic import parse
    from pymbolic.primitives import Quotient

    exprs = [
            2j,
            parse("x**y"),
            Quotient(1, 2),
            ]
    for expr in exprs:
        result = knl.eval_expr(expr)
        round_trips_correctly = result == expr
        if not round_trips_correctly:
            print("ORIGINAL:")
            print("")
            print(expr)
            print("")
            print("POST-MAXIMA:")
            print("")
            print(result)
        assert round_trips_correctly


def test_lax_round_trip(knl):
    from pymbolic.interop.maxima import MaximaParser
    k_setup = [
            "k:1/(sqrt((x0-(a+t*b))^2+(y0-(c+t*d))^2))",
            "result:sum(diff(k, t,deg)*t^deg,deg,0,4)",
            ]
    parsed = MaximaParser()(
            knl.clean_eval_str_with_setup(k_setup, "result"))

    assert knl.clean_eval_expr_with_setup(
            k_setup + [("result2", parsed)],
            "ratsimp(result-result2)") == 0


def test_diff():
    pytest.importorskip("pexpect")

    from pymbolic.interop.maxima import diff
    from pymbolic import parse
    diff(parse("sqrt(x**2+y**2)"), parse("x"))


@mark_test.xfail
def test_long_command(knl):
    from pymbolic.interop.maxima import set_debug
    set_debug(4)
    knl.eval_str("+".join(["1"]*16384))


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
