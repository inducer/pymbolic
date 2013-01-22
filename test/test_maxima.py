import pytest
from pytools.test import mark_test

def test_kernel():
    pytest.importorskip("pexpect")

    from pymbolic.maxima import MaximaKernel
    knl = MaximaKernel()
    knl.exec_str("k:1/(sqrt((x0-(a+t*b))^2+(y0-(c+t*d))^2+(z0-(e+t*f))^2))")
    knl.eval_str("sum(diff(k, t,deg)*t^deg,deg,0,6)")
    assert knl.eval_str("2+2").strip() == "4"
    knl.shutdown()

def pytest_funcarg__knl(request):
    pytest.importorskip("pexpect")

    from pymbolic.maxima import MaximaKernel
    knl = MaximaKernel()
    request.addfinalizer(knl.shutdown)
    return knl

def test_setup(knl):
    pytest.importorskip("pexpect")

    knl.clean_eval_str_with_setup(
            ["k:1/(sqrt((x0-(a+t*b))^2+(y0-(c+t*d))^2+(z0-(e+t*f))^2))"],
            "sum(diff(k, t,deg)*t^deg,deg,0,6)")

def test_error(knl):
    from pymbolic.maxima import MaximaError
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
            print "ORIGINAL:"
            print
            print expr
            print
            print "POST-MAXIMA:"
            print
            print result
        assert round_trips_correctly

def test_lax_round_trip(knl):
    from pymbolic.maxima import MaximaParser
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

    from pymbolic.maxima import diff
    from pymbolic import parse
    diff(parse("sqrt(x**2+y**2)"), parse("x"))

@mark_test.xfail
def test_long_command(knl):
    from pymbolic.maxima import set_debug
    set_debug(4)
    knl.eval_str("+".join(["1"]*16384))

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
