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

import pymbolic.primitives as prim
import pytest

from pymbolic.mapper import IdentityMapper

try:
    reduce
except NameError:
    from functools import reduce


def test_integer_power():
    from pymbolic.algorithm import integer_power

    for base, expn in [
            (17, 5),
            (17, 2**10),
            (13, 20),
            (13, 1343),
            ]:
        assert base**expn == integer_power(base, expn)


def test_expand():
    from pymbolic import var, expand

    x = var("x")
    u = (x+1)**5
    expand(u)


def test_substitute():
    from pymbolic import parse, substitute, evaluate
    u = parse("5+x.min**2")
    xmin = parse("x.min")
    assert evaluate(substitute(u, {xmin: 25})) == 630


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


def test_structure_preservation():
    x = prim.Sum((5, 7))
    from pymbolic.mapper import IdentityMapper
    x2 = IdentityMapper()(x)
    assert x == x2


def test_sympy_interaction():
    pytest.importorskip("sympy")

    import sympy as sp

    x, y = sp.symbols("x y")
    f = sp.symbols("f")

    s1_expr = 1/f(x/sp.sqrt(x**2+y**2)).diff(x, 5)

    from pymbolic.sympy_interface import (
            SympyToPymbolicMapper,
            PymbolicToSympyMapper)
    s2p = SympyToPymbolicMapper()
    p2s = PymbolicToSympyMapper()

    p1_expr = s2p(s1_expr)
    s2_expr = p2s(p1_expr)

    assert sp.ratsimp(s1_expr - s2_expr) == 0

    p2_expr = s2p(s2_expr)
    s3_expr = p2s(p2_expr)

    assert sp.ratsimp(s1_expr - s3_expr) == 0


# {{{ fft

def test_fft_with_floats():
    numpy = pytest.importorskip("numpy")
    import numpy.linalg as la

    from pymbolic.algorithm import fft, ifft

    for n in [2**i for i in range(4, 10)]+[17, 12, 948]:
        a = numpy.random.rand(n) + 1j*numpy.random.rand(n)
        f_a = fft(a)
        a2 = ifft(f_a)
        assert la.norm(a-a2) < 1e-10

        f_a_numpy = numpy.fft.fft(a)
        assert la.norm(f_a-f_a_numpy) < 1e-10


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
    numpy = pytest.importorskip("numpy")

    from pymbolic import var
    from pymbolic.algorithm import fft, sym_fft

    vars = numpy.array([var(chr(97+i)) for i in range(16)], dtype=object)
    print(vars)

    print(fft(vars))
    traced_fft = sym_fft(vars)

    from pymbolic.mapper.stringifier import PREC_NONE
    from pymbolic.mapper.c_code import CCodeMapper
    ccm = CCodeMapper()

    code = [ccm(tfi, PREC_NONE) for tfi in traced_fft]

    for cse_name, cse_str in enumerate(ccm.cse_name_list):
        print("%s = %s" % (cse_name, cse_str))

    for i, line in enumerate(code):
        print("result[%d] = %s" % (i, line))

# }}}


def test_sparse_multiply():
    numpy = pytest.importorskip("numpy")
    pytest.importorskip("scipy")
    import scipy.sparse as ss

    la = numpy.linalg

    mat = numpy.random.randn(10, 10)
    s_mat = ss.csr_matrix(mat)

    vec = numpy.random.randn(10)
    mat_vec = s_mat*vec

    from pymbolic.algorithm import csr_matrix_multiply
    mat_vec_2 = csr_matrix_multiply(s_mat, vec)

    assert la.norm(mat_vec-mat_vec_2) < 1e-14


# {{{ parser

def test_parser():
    from pymbolic import parse
    parse("(2*a[1]*b[1]+2*a[0]*b[0])*(hankel_1(-1,sqrt(a[1]**2+a[0]**2)*k) "
            "-hankel_1(1,sqrt(a[1]**2+a[0]**2)*k))*k /(4*sqrt(a[1]**2+a[0]**2)) "
            "+hankel_1(0,sqrt(a[1]**2+a[0]**2)*k)")
    print(repr(parse("d4knl0")))
    print(repr(parse("0.")))
    print(repr(parse("0.e1")))
    print(repr(parse("0.e1")))
    print(repr(parse("a >= 1")))
    print(repr(parse("a <= 1")))

    print(repr(parse(":")))
    print(repr(parse("1:")))
    print(repr(parse(":2")))
    print(repr(parse("1:2")))
    print(repr(parse("::")))
    print(repr(parse("1::")))
    print(repr(parse(":1:")))
    print(repr(parse("::1")))
    print(repr(parse("3::1")))
    print(repr(parse(":5:1")))
    print(repr(parse("3:5:1")))

    print(parse("3::1"))

    assert parse("e1") == prim.Variable("e1")
    assert parse("d1") == prim.Variable("d1")

    from pymbolic import variables
    f, x, y, z = variables("f x y z")
    assert parse("f((x,y),z)") == f((x, y), z)
    assert parse("f((x,),z)") == f((x,), z)
    assert parse("f(x,(y,z),z)") == f(x, (y, z), z)

# }}}


# {{{ geometric algebra

@pytest.mark.parametrize("dims", [2, 3, 4, 5])
# START_GA_TEST
def test_geometric_algebra(dims):
    pytest.importorskip("numpy")

    import numpy as np
    from pymbolic.geometric_algebra import MultiVector as MV

    vec1 = MV(np.random.randn(dims))
    vec2 = MV(np.random.randn(dims))
    vec3 = MV(np.random.randn(dims))
    vec4 = MV(np.random.randn(dims))
    vec5 = MV(np.random.randn(dims))

    # Fundamental identity
    assert ((vec1 ^ vec2) + (vec1 | vec2)).close_to(vec1*vec2)

    # Antisymmetry
    assert (vec1 ^ vec2 ^ vec3).close_to(- vec2 ^ vec1 ^ vec3)

    vecs = [vec1, vec2, vec3, vec4, vec5]

    if len(vecs) > dims:
        from operator import xor as outer
        assert reduce(outer, vecs).close_to(0)

    assert (vec1.inv()*vec1).close_to(1)
    assert (vec1*vec1.inv()).close_to(1)
    assert ((1/vec1)*vec1).close_to(1)
    assert (vec1/vec1).close_to(1)

    for a, b, c in [
            (vec1, vec2, vec3),
            (vec1*vec2, vec3, vec4),
            (vec1, vec2*vec3, vec4),
            (vec1, vec2, vec3*vec4),
            (vec1, vec2, vec3*vec4*vec5),
            (vec1, vec2*vec1, vec3*vec4*vec5),
            ]:

        # Associativity
        assert ((a*b)*c).close_to(a*(b*c))
        assert ((a ^ b) ^ c).close_to(a ^ (b ^ c))
        # The inner product is not associative.

        # scalar product
        assert ((c*b).project(0)) .close_to(b.scalar_product(c))
        assert ((c.rev()*b).project(0)) .close_to(b.rev().scalar_product(c))
        assert ((b.rev()*b).project(0)) .close_to(b.norm_squared())

        assert b.norm_squared() >= 0
        assert c.norm_squared() >= 0

        # Cauchy's inequality
        assert b.scalar_product(c) <= abs(b)*abs(c) + 1e-13

        # contractions

        # (3.18) in [DFM]
        assert abs(b.scalar_product(a ^ c) - (b >> a).scalar_product(c)) < 1e-13

        # duality, (3.20) in [DFM]
        assert ((a ^ b) << c) .close_to(a << (b << c))

        # two definitions of the dual agree: (1.2.26) in [HS]
        # and (sec 3.5.3) in [DFW]
        assert (c << c.I.rev()).close_to(c | c.I.rev())

        # inverse
        for div in list(b.gen_blades()) + [vec1, vec1.I]:
            assert (div.inv()*div).close_to(1)
            assert (div*div.inv()).close_to(1)
            assert ((1/div)*div).close_to(1)
            assert (div/div).close_to(1)
            assert ((c/div)*div).close_to(c)
            assert ((c*div)/div).close_to(c)

        # reverse properties (Sec 2.9.5 [DFM])
        assert c.rev().rev() == c
        assert (b ^ c).rev() .close_to((c.rev() ^ b.rev()))

        # dual properties
        # (1.2.26) in [HS]
        assert c.dual() .close_to(c | c.I.rev())
        assert c.dual() .close_to(c*c.I.rev())

        # involution properties (Sec 2.9.5 DFW)
        assert c.invol().invol() == c
        assert (b ^ c).invol() .close_to((b.invol() ^ c.invol()))

        # commutator properties

        # Jacobi identity (1.1.56c) in [HS] or (8.2) in [DFW]
        assert (a.x(b.x(c)) + b.x(c.x(a)) + c.x(a.x(b))).close_to(0)

        # (1.57) in [HS]
        assert a.x(b*c) .close_to(a.x(b)*c + b*a.x(c))
# END_GA_TEST

# }}}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from py.test.cmdline import main
        main([__file__])

# vim: fdm=marker
