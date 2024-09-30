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

import pytest

from pymbolic.interop.maxima import MaximaKernel


# {{{ check for maxima

def _check_maxima():
    global MAXIMA_UNAVAILABLE

    import os
    executable = os.environ.get("PYMBOLIC_MAXIMA_EXECUTABLE", "maxima")

    try:
        knl = MaximaKernel(executable=executable)
        MAXIMA_UNAVAILABLE = False
        knl.shutdown()
    except (ImportError, RuntimeError):
        MAXIMA_UNAVAILABLE = True


_check_maxima()

# }}}


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
def test_kernel():
    knl = MaximaKernel()
    knl.exec_str("k:1/(sqrt((x0-(a+t*b))^2+(y0-(c+t*d))^2+(z0-(e+t*f))^2))")
    knl.eval_str("sum(diff(k, t,deg)*t^deg,deg,0,6)")
    assert knl.eval_str("2+2").strip() == "4"
    knl.shutdown()


@pytest.fixture
def knl(request):
    knl = MaximaKernel()
    request.addfinalizer(knl.shutdown)
    return knl


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
def test_setup(knl):
    knl.clean_eval_str_with_setup(
            ["k:1/(sqrt((x0-(a+t*b))^2+(y0-(c+t*d))^2+(z0-(e+t*f))^2))"],
            "sum(diff(k, t,deg)*t^deg,deg,0,6)")


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
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


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
def test_strict_round_trip(knl):
    from pymbolic import parse
    from pymbolic.primitives import Quotient

    exprs = [
            2j,
            parse("x**y"),
            Quotient(1, 2),
            parse("exp(x)")
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


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
def test_lax_round_trip(knl):
    from pymbolic.interop.maxima import MaximaParser
    k_setup = [
            "k:1/(sqrt((x0-(a+t*b))^2+(y0-(c+t*d))^2))",
            "result:sum(diff(k, t,deg)*t^deg,deg,0,4)",
            ]
    parsed = MaximaParser()(
            knl.clean_eval_str_with_setup(k_setup, "result"))

    assert knl.clean_eval_expr_with_setup(
            [*k_setup, ("result2", parsed)],
            "ratsimp(result-result2)") == 0


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
def test_parse_matrix(knl):
    z = knl.clean_eval_str_with_setup([
        "A:matrix([1,2+0.3*dt], [3,4])",
        "B:matrix([1,1], [0,1])",
        ],
        "A.B")

    from pymbolic.interop.maxima import MaximaParser
    print(MaximaParser()(z))


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
def test_diff():
    from pymbolic import parse
    from pymbolic.interop.maxima import diff
    diff(parse("sqrt(x**2+y**2)"), parse("x"))


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
def test_long_command(knl):
    # Seems to fail with an encoding error on pexpect 4.8 and Py3.8.
    # -AK, 2020-07-13
    # from pymbolic.interop.maxima import set_debug
    # set_debug(4)
    knl.eval_str("+".join(["1"]*16384))


@pytest.mark.skipif(MAXIMA_UNAVAILABLE, reason="maxima cannot be launched")
def test_restart(knl):
    knl = MaximaKernel()
    knl.restart()
    knl.eval_str("1")
    knl.shutdown()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from pytest import main
        main([__file__])
