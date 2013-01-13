from __future__ import division
import pymbolic.primitives as prim




def test_expand():
    from pymbolic import var, expand

    x = var("x")
    u = (x+1)**5
    expand(u)




def test_substitute():
    from pymbolic import parse, substitute, evaluate
    u = parse("5+x.min**2")
    xmin = parse("x.min")
    assert evaluate(substitute(u, {xmin:25})) == 630




def test_fft_with_floats():
    import py.test
    numpy = py.test.importorskip("numpy")
    import numpy.linalg as la

    from pymbolic.algorithm import fft, ifft

    for n in [2**i for i in range(4, 10)]+[17, 12, 948]:
        a = numpy.random.rand(n) + 1j*numpy.random.rand(n)
        f_a = fft(a)
        a2 = ifft(f_a)
        assert la.norm(a-a2) < 1e-10

        f_a_numpy = numpy.fft.fft(a)
        assert la.norm(f_a-f_a_numpy) < 1e-10




from pymbolic.mapper import IdentityMapper
class NearZeroKiller(IdentityMapper):
    def map_constant(self, expr):
        if isinstance(expr, complex):
            r = expr.real
            i = expr.imag
            if abs(r) < 1e-15:
                r = 0
            if abs(i) < 1e-15:
                i = 0
            return complex(r, i)
        else:
            return expr





def test_fft():
    import py.test
    numpy = py.test.importorskip("numpy")

    from pymbolic import var
    from pymbolic.algorithm import fft, sym_fft

    vars = numpy.array([var(chr(97+i)) for i in range(16)], dtype=object)
    print vars

    print fft(vars)
    traced_fft = sym_fft(vars)

    from pymbolic.mapper.stringifier import PREC_NONE
    from pymbolic.mapper.c_code import CCodeMapper
    ccm = CCodeMapper()

    code = [ccm(tfi, PREC_NONE) for tfi in traced_fft]

    for cse_name, cse_str in enumerate(ccm.cse_name_list):
        print "%s = %s" % (cse_name, cse_str)

    for i, line in enumerate(code):
        print "result[%d] = %s" % (i, line)




def test_sparse_multiply():
    import py.test
    numpy = py.test.importorskip("numpy")
    py.test.importorskip("scipy")
    import scipy.sparse as ss

    la = numpy.linalg

    mat = numpy.random.randn(10, 10)
    s_mat = ss.csr_matrix(mat)

    vec = numpy.random.randn(10)
    mat_vec = s_mat*vec

    from pymbolic.algorithm import csr_matrix_multiply
    mat_vec_2 = csr_matrix_multiply(s_mat, vec)

    assert la.norm(mat_vec-mat_vec_2) < 1e-14



def test_no_comparison():
    from pymbolic import parse

    x = parse("17+3*x") 
    y = parse("12-5*y")

    def expect_typeerror(f):
        try:
            f()
        except TypeError:
            pass
        else:
            assert False

    expect_typeerror(lambda: x < y)
    expect_typeerror(lambda: x <= y)
    expect_typeerror(lambda: x > y)
    expect_typeerror(lambda: x >= y)




def test_parser():
    from pymbolic import parse
    parse("(2*a[1]*b[1]+2*a[0]*b[0])*(hankel_1(-1,sqrt(a[1]**2+a[0]**2)*k) "
            "-hankel_1(1,sqrt(a[1]**2+a[0]**2)*k))*k /(4*sqrt(a[1]**2+a[0]**2)) "
            "+hankel_1(0,sqrt(a[1]**2+a[0]**2)*k)")
    print repr(parse("d4knl0"))
    print repr(parse("0."))
    print repr(parse("0.e1"))
    print repr(parse("0.e1"))
    print repr(parse("a >= 1"))
    print repr(parse("a <= 1"))

    print repr(parse(":"))
    print repr(parse("1:"))
    print repr(parse(":2"))
    print repr(parse("1:2"))
    print repr(parse("::"))
    print repr(parse("1::"))
    print repr(parse(":1:"))
    print repr(parse("::1"))
    print repr(parse("3::1"))
    print repr(parse(":5:1"))
    print repr(parse("3:5:1"))

    print parse("3::1")

    assert parse("e1") == prim.Variable("e1")
    assert parse("d1") == prim.Variable("d1")

    from pymbolic import variables
    f, x, y, z = variables("f x y z")
    assert parse("f((x,y),z)") == f((x,y),z)
    assert parse("f((x,),z)") == f((x,),z)
    assert parse("f(x,(y,z),z)") == f(x,(y,z),z)




def test_structure_preservation():
    x = prim.Sum((5, 7))
    from pymbolic.mapper import IdentityMapper
    x2 = IdentityMapper()(x)
    assert x == x2






if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])
