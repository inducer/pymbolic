from __future__ import annotations

from pymbolic.mapper.evaluator import evaluate_kw
from pymbolic.mapper.flattener import FlattenMapper
from pymbolic.mapper.stringifier import StringifyMapper
from pymbolic.typing import Expression


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

import logging
from functools import reduce

import pytest
from testlib import generate_random_expression

from pytools.lex import ParseError

import pymbolic.primitives as prim
from pymbolic import parse
from pymbolic.mapper import IdentityMapper, WalkMapper
from pymbolic.mapper.dependency import CachedDependencyMapper, DependencyMapper


logger = logging.getLogger(__name__)


# {{{ utilities

def assert_parsed_same_as_python(expr_str):
    # makes sure that has only one line
    expr_str, = expr_str.split("\n")

    import ast

    from pymbolic.interop.ast import ASTToPymbolic
    ast2p = ASTToPymbolic()

    try:
        expr_parsed_by_python = ast2p(ast.parse(expr_str).body[0].value)
    except SyntaxError:
        with pytest.raises(ParseError):
            parse(expr_str)
    else:
        expr_parsed_by_pymbolic = parse(expr_str)
        assert expr_parsed_by_python == expr_parsed_by_pymbolic


def assert_parse_roundtrip(expr_str):
    from pymbolic.mapper.stringifier import StringifyMapper
    expr = parse(expr_str)
    strified = StringifyMapper()(expr)

    assert strified == expr_str, (strified, expr_str)

# }}}


EXPRESSION_COLLECTION = [
    parse("(x[2]+y.data)*(x+z)**3"),
    parse("(~x)//2 | (y >> 2) & (z << 3)"),
    parse("x and (not y or z)"),
    parse("x if not (y and z) else x+1"),
]


# {{{ test_integer_power

def test_integer_power():
    from pymbolic.algorithm import integer_power

    for base, expn in [
            (17, 5),
            (17, 2**10),
            (13, 20),
            (13, 1343),
            ]:
        assert base**expn == integer_power(base, expn)

# }}}


# {{{ test_expand

def test_expand():
    from pymbolic import expand, var

    x = var("x")
    u = (x+1)**5
    expand(u)

# }}}


# {{{ test_substitute

def test_substitute():
    from pymbolic import evaluate, parse, substitute
    u = parse("5+x.min**2")
    xmin = parse("x.min")
    assert evaluate(substitute(u, {xmin: 25})) == 630

# }}}


# {{{ test_no_comparison

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
            raise AssertionError

    expect_typeerror(lambda: x < y)
    expect_typeerror(lambda: x <= y)
    expect_typeerror(lambda: x > y)
    expect_typeerror(lambda: x >= y)

# }}}


# {{{ test_structure_preservation

def test_structure_preservation():
    x = prim.Sum((5, 7))
    x2 = IdentityMapper()(x)
    assert x == x2

# }}}


# {{{ test_sympy_interaction

def test_sympy_interaction():
    pytest.importorskip("sympy")

    import sympy as sp

    x, y = sp.symbols("x y")
    f = sp.Function("f")

    s1_expr = 1/f(x/sp.sqrt(x**2+y**2)).diff(x, 5)  # pylint:disable=not-callable

    from pymbolic.interop.sympy import PymbolicToSympyMapper, SympyToPymbolicMapper
    s2p = SympyToPymbolicMapper()
    p2s = PymbolicToSympyMapper()

    p1_expr = s2p(s1_expr)
    s2_expr = p2s(p1_expr)

    assert sp.ratsimp(s1_expr - s2_expr) == 0

    p2_expr = s2p(s2_expr)
    s3_expr = p2s(p2_expr)

    assert sp.ratsimp(s1_expr - s3_expr) == 0

# }}}


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
    logger.info("vars: %s", vars)

    logger.info("fft: %s", fft(vars))
    traced_fft = sym_fft(vars)

    from pymbolic.mapper.c_code import CCodeMapper
    from pymbolic.mapper.stringifier import PREC_NONE
    ccm = CCodeMapper()

    code = [ccm(tfi, PREC_NONE) for tfi in traced_fft]

    for cse_name, cse_str in enumerate(ccm.cse_name_list):
        logger.info("%s = %s", cse_name, cse_str)

    for i, line in enumerate(code):
        logger.info("result[%d] = %s", i, line)

# }}}


# {{{ test_sparse_multiply

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

# }}}


# {{{ parser

def test_parser():
    from pymbolic import parse
    parse("(2*a[1]*b[1]+2*a[0]*b[0])*(hankel_1(-1,sqrt(a[1]**2+a[0]**2)*k) "
            "-hankel_1(1,sqrt(a[1]**2+a[0]**2)*k))*k /(4*sqrt(a[1]**2+a[0]**2)) "
            "+hankel_1(0,sqrt(a[1]**2+a[0]**2)*k)")
    logger.info("%r", parse("d4knl0"))
    logger.info("%r", parse("0."))
    logger.info("%r", parse("0.e1"))
    assert parse("0.e1") == 0
    assert parse("1e-12") == 1e-12
    logger.info("%r", parse("a >= 1"))
    logger.info("%r", parse("a <= 1"))

    logger.info("%r", parse(":"))
    logger.info("%r", parse("1:"))
    logger.info("%r", parse(":2"))
    logger.info("%r", parse("1:2"))
    logger.info("%r", parse("::"))
    logger.info("%r", parse("1::"))
    logger.info("%r", parse(":1:"))
    logger.info("%r", parse("::1"))
    logger.info("%r", parse("3::1"))
    logger.info("%r", parse(":5:1"))
    logger.info("%r", parse("3:5:1"))

    assert_parse_roundtrip("()")
    assert_parse_roundtrip("(3,)")

    assert_parse_roundtrip("[x + 3, 3, 5]")
    assert_parse_roundtrip("[]")
    assert_parse_roundtrip("[x]")

    assert_parse_roundtrip("g[i, k] + 2.0*h[i, k]")
    parse("g[i,k]+(+2.0)*h[i, k]")

    logger.info("%r", parse("a - b - c"))
    logger.info("%r", parse("-a - -b - -c"))
    logger.info("%r", parse("- - - a - - - - b - - - - - c"))

    logger.info("%r", parse("~(a ^ b)"))
    logger.info("%r", parse("(a | b) | ~(~a & ~b)"))

    logger.info("%r", parse("3 << 1"))
    logger.info("%r", parse("1 >> 3"))

    logger.info(parse("3::1"))

    assert parse("e1") == prim.Variable("e1")
    assert parse("d1") == prim.Variable("d1")

    from pymbolic import variables
    f, x, y, z = variables("f x y z")
    assert parse("f((x,y),z)") == f((x, y), z)
    assert parse("f((x,),z)") == f((x,), z)
    assert parse("f(x,(y,z),z)") == f(x, (y, z), z)

    assert parse("f(x,(y,z),z, name=15)") == f(x, (y, z), z, name=15)
    assert parse("f(x,(y,z),z, name=15, name2=17)") == f(
            x, (y, z), z, name=15, name2=17)

    assert_parsed_same_as_python("5+i if i>=0 else (0 if i<-1 else 10)")
    assert_parsed_same_as_python("0 if 1 if 2 else 3 else 4")
    assert_parsed_same_as_python("0 if (1 if 2 else 3) else 4")
    assert_parsed_same_as_python("(2, 3,)")
    assert_parsed_same_as_python("-3**0.5")
    assert_parsed_same_as_python("1/2/7")

    with pytest.deprecated_call():
        parse("1+if(0, 1, 2)")

    assert eval(str(parse("1729 if True or False else 42"))) == 1729

# }}}


# {{{ test_mappers

def test_mappers():
    from pymbolic import variables
    f, x, y, z = variables("f x y z")

    for expr in [
            f(x, (y, z), name=z**2)
            ]:
        str(expr)
        IdentityMapper()(expr)
        WalkMapper()(expr)
        DependencyMapper()(expr)


# }}}


# {{{ test_func_dep_consistency

def test_func_dep_consistency():
    from pymbolic import var
    f = var("f")
    x = var("x")
    dep_map = DependencyMapper(include_calls="descend_args")
    assert dep_map(f(x)) == {x}
    assert dep_map(f(x=x)) == {x}

# }}}


# {{{ test_conditions

def test_conditions():
    from pymbolic import var
    x = var("x")
    y = var("y")
    assert str(x.eq(y).and_(x.le(5))) == "x == y and x <= 5"

# }}}


# {{{ test_graphviz

def test_graphviz():
    from pymbolic import parse
    expr = parse("(2*a[1]*b[1]+2*a[0]*b[0])*(hankel_1(-1,sqrt(a[1]**2+a[0]**2)*k) "
            "-hankel_1(1,sqrt(a[1]**2+a[0]**2)*k))*k /(4*sqrt(a[1]**2+a[0]**2)) "
            "+hankel_1(0,sqrt(a[1]**2+a[0]**2)*k)")

    from pymbolic.mapper.graphviz import GraphvizMapper
    gvm = GraphvizMapper()
    gvm(expr)
    logger.info("%s", gvm.get_dot_code())

# }}}


# {{{ geometric algebra

@pytest.mark.parametrize("dims", [2, 3, 4, 5])
# START_GA_TEST
def test_geometric_algebra(dims):
    pytest.importorskip("numpy")

    import numpy as np

    from pymbolic.geometric_algebra import MultiVector as MV  # noqa

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
        assert abs(b.scalar_product(a ^ c) - (b >> a).scalar_product(c)) < 1e-12

        # duality, (3.20) in [DFM]
        assert ((a ^ b) << c) .close_to(a << (b << c))

        # two definitions of the dual agree: (1.2.26) in [HS]
        # and (sec 3.5.3) in [DFW]
        assert (c << c.I.rev()).close_to(c | c.I.rev())

        # inverse
        for div in [*b.gen_blades(), vec1, vec1.I]:
            assert (div.inv()*div).close_to(1)
            assert (div*div.inv()).close_to(1)
            assert ((1/div)*div).close_to(1)
            assert (div/div).close_to(1)
            assert ((c/div)*div).close_to(c)
            assert ((c*div)/div).close_to(c)

        # reverse properties (Sec 2.9.5 [DFM])
        assert c.rev().rev() == c
        assert (b ^ c).rev() .close_to(c.rev() ^ b.rev())

        # dual properties
        # (1.2.26) in [HS]
        assert c.dual() .close_to(c | c.I.rev())
        assert c.dual() .close_to(c*c.I.rev())

        # involution properties (Sec 2.9.5 DFW)
        assert c.invol().invol() == c
        assert (b ^ c).invol() .close_to(b.invol() ^ c.invol())

        # commutator properties

        # Jacobi identity (1.1.56c) in [HS] or (8.2) in [DFW]
        assert (a.x(b.x(c)) + b.x(c.x(a)) + c.x(a.x(b))).close_to(0)

        # (1.57) in [HS]
        assert a.x(b*c) .close_to(a.x(b)*c + b*a.x(c))
# END_GA_TEST

# }}}


# {{{ test_ast_interop

def test_ast_interop():
    src = """
    def f():
        xx = 3*y + z * (12 if x < 13 else 13)
        yy = f(x, y=y)
    """

    import ast
    mod = ast.parse(src.replace("\n    ", "\n"))

    logger.info("%s", ast.dump(mod))

    from pymbolic.interop.ast import ASTToPymbolic
    ast2p = ASTToPymbolic()

    for f in mod.body:
        if not isinstance(f, ast.FunctionDef):
            continue

        for stmt in f.body:
            if not isinstance(stmt, ast.Assign):
                continue

            lhs, = stmt.targets
            lhs = ast2p(lhs)
            rhs = ast2p(stmt.value)

            logger.info("lhs %s rhs %s", lhs, rhs)

# }}}


# {{{ test_compile

def test_compile():
    from pymbolic import compile, parse
    code = compile(parse("x ** y"), ["x", "y"])
    assert code(2, 5) == 32

    # Test pickling of compiled code.
    import pickle
    code = pickle.loads(pickle.dumps(code))
    assert code(3, 3) == 27

# }}}


# {{{ test_pickle

def test_pickle():
    from pickle import dumps, loads
    for expr in EXPRESSION_COLLECTION:
        pickled = loads(dumps(expr))
        assert hash(expr) == hash(pickled)
        assert expr == pickled


class OldTimeyExpression(prim.ExpressionNode):
    init_arg_names = ()

    def __getinitargs__(self):
        return ()


def test_pickle_backward_compat():
    from pickle import dumps, loads

    expr = 3*OldTimeyExpression()
    pickled = loads(dumps(expr))
    with pytest.warns(DeprecationWarning):
        assert hash(expr) == hash(pickled)
    with pytest.warns(DeprecationWarning):
        assert expr == pickled
# }}}


# {{{ test_unifier

def test_unifier():
    from pymbolic import var
    from pymbolic.mapper.unifier import UnidirectionalUnifier
    a, b, c, d, e, f = (var(s) for s in "abcdef")

    def match_found(records, eqns):
        for record in records:
            if eqns <= set(record.equations):
                return True
        return False

    recs = UnidirectionalUnifier("abc")(a+b*c, d+e*f)
    assert len(recs) == 2
    assert match_found(recs, {(a, d), (b, e), (c, f)})
    assert match_found(recs, {(a, d), (b, f), (c, e)})

    recs = UnidirectionalUnifier("abc")(a+b, d+e+f)
    assert len(recs) == 6
    assert match_found(recs, {(a, d), (b, e+f)})
    assert match_found(recs, {(a, e), (b, d+f)})
    assert match_found(recs, {(a, f), (b, d+e)})
    assert match_found(recs, {(b, d), (a, e+f)})
    assert match_found(recs, {(b, e), (a, d+f)})
    assert match_found(recs, {(b, f), (a, d+e)})

    vals = [var("v" + str(i)) for i in range(100)]
    recs = UnidirectionalUnifier("a")(sum(vals[1:]) + a, sum(vals))
    assert len(recs) == 1
    assert match_found(recs, {(a, var("v0"))})

    recs = UnidirectionalUnifier("abc")(a+b+c, d+e)
    assert len(recs) == 0

    recs = UnidirectionalUnifier("abc")(f(a+b, f(a+c)), f(b+c, f(b+d)))
    assert len(recs) == 1
    assert match_found(recs, {(a, b), (b, c), (c, d)})

# }}}


# {{{ test_long_sympy_mapping

def test_long_sympy_mapping():
    sp = pytest.importorskip("sympy")
    from pymbolic.interop.sympy import SympyToPymbolicMapper
    SympyToPymbolicMapper()(sp.sympify(int(10**20)))
    SympyToPymbolicMapper()(sp.sympify(10))

# }}}


# {{{ test_stringifier_preserve_shift_order

def test_stringifier_preserve_shift_order():
    for expr in [
            parse("(a << b) >> 2"),
            parse("a << (b >> 2)")
            ]:
        assert parse(str(expr)) == expr

# }}}


# {{{ test_latex_mapper

LATEX_TEMPLATE = r"""\documentclass{article}
\usepackage{amsmath}

\begin{document}
%s
\end{document}"""


def test_latex_mapper():
    from pymbolic import parse
    from pymbolic.mapper.stringifier import LaTeXMapper, StringifyMapper

    tm = LaTeXMapper()
    sm = StringifyMapper()

    equations = []

    def add(expr):
        # Add an equation to the list of tests.
        equations.append(r"\[{}\] % from: {}".format(tm(expr), sm(expr)))

    add(parse("a * b + c"))
    add(parse("f(a,b,c)"))
    add(parse("a ** b ** c"))
    add(parse("(a | b) ^ ~c"))
    add(parse("a << b"))
    add(parse("a >> b"))
    add(parse("a[i,j,k]"))
    add(parse("a[1:3]"))
    add(parse("a // b"))
    add(parse("not (a or b) and c"))
    add(parse("(a % b) % c"))
    add(parse("(a >= b) or (b <= c)"))
    add(prim.Min((1,)) + prim.Max((1, 2)))
    add(prim.Substitution(prim.Variable("x") ** 2, ("x",), (2,)))
    add(prim.Derivative(parse("x**2"), ("x",)))

    # Run LaTeX and ensure the file compiles.
    import os
    import shutil
    import subprocess
    import tempfile

    latex_dir = tempfile.mkdtemp("pymbolic")

    try:
        tex_file_path = os.path.join(latex_dir, "input.tex")

        with open(tex_file_path, "w") as tex_file:
            contents = LATEX_TEMPLATE % "\n".join(equations)
            tex_file.write(contents)

        try:
            subprocess.check_output(
                    ["latex",
                     "-interaction=nonstopmode",
                     "-output-directory=%s" % latex_dir,
                     tex_file_path],
                    universal_newlines=True)
        except FileNotFoundError:
            pytest.skip("latex command not found")
        except subprocess.CalledProcessError as err:
            raise AssertionError(str(err.output)) from None

    finally:
        shutil.rmtree(latex_dir)

# }}}


# {{{ test_flop_counter

def test_flop_counter():
    x = prim.Variable("x")
    y = prim.Variable("y")
    z = prim.Variable("z")

    subexpr = prim.make_common_subexpression(3 * (x**2 + y + z))
    expr = 3*subexpr + subexpr

    from pymbolic.mapper.flop_counter import CSEAwareFlopCounter, FlopCounter
    assert FlopCounter()(expr) == 4 * 2 + 2

    assert CSEAwareFlopCounter()(expr) == 4 + 2

# }}}


# {{{ test_make_sym_vector

def test_make_sym_vector():
    numpy = pytest.importorskip("numpy")
    from pymbolic.primitives import make_sym_vector

    assert len(make_sym_vector("vec", 2)) == 2
    assert len(make_sym_vector("vec", numpy.int32(2))) == 2
    assert len(make_sym_vector("vec", [1, 2, 3])) == 3

# }}}


# {{{ test_multiplicative_stringify_preserves_association

def test_multiplicative_stringify_preserves_association():
    for inner in ["*", " / ", " // ", " % "]:
        for outer in ["*", " / ", " // ", " % "]:
            if outer == inner:
                continue

            assert_parse_roundtrip(f"x{outer}(y{inner}z)")
            assert_parse_roundtrip(f"(y{inner}z){outer}x")

    assert_parse_roundtrip("(-1)*(((-1)*x) / 5)")

# }}}


# {{{ test_differentiator_flags_for_nonsmooth_and_discontinuous

def test_differentiator_flags_for_nonsmooth_and_discontinuous():
    import pymbolic.functions as pf
    from pymbolic.mapper.differentiator import differentiate

    x = prim.Variable("x")

    with pytest.raises(ValueError):
        differentiate(pf.fabs(x), x)

    result = differentiate(pf.fabs(x), x, allowed_nonsmoothness="continuous")
    assert result == pf.sign(x)

    with pytest.raises(ValueError):
        differentiate(pf.sign(x), x)

    result = differentiate(pf.sign(x), x, allowed_nonsmoothness="discontinuous")
    assert result == 0

# }}}


# {{{ test_diff_cse

def test_diff_cse():
    from pymbolic import evaluate_kw
    from pymbolic.mapper.differentiator import differentiate

    m = prim.Variable("math")

    x = prim.Variable("x")
    cse = prim.make_common_subexpression(x**2 + 1)
    expr = m.attr("exp")(cse)*m.attr("sin")(cse**2)

    diff_result = differentiate(expr, x)

    import math
    from functools import partial
    my_eval = partial(evaluate_kw, math=math)

    x0 = 5
    h = 0.001
    fprime = my_eval(diff_result, x=x0)
    fprime_num_1 = (my_eval(expr, x=x0+h) - my_eval(expr, x=x0-h))/(2*h)
    fprime_num_2 = (my_eval(expr, x=x0+0.5*h) - my_eval(expr, x=x0-0.5*h))/h

    err1 = abs(fprime - fprime_num_1)/abs(fprime)
    err2 = abs(fprime - fprime_num_2)/abs(fprime)

    assert err2 < 1.1 * 0.5**2 * err1

# }}}


# {{{ test_coefficient_collector

def test_coefficient_collector():
    from pymbolic.mapper.coefficient import CoefficientCollector
    x = prim.Variable("x")
    y = prim.Variable("y")
    z = prim.Variable("z")

    cc = CoefficientCollector([x.name, y.name])
    assert cc(2*x + y) == {x: 2, y: 1}
    assert cc(2*x + y - z) == {x: 2, y: 1, 1: -z}
    assert cc(x/2 + z**2) == {x: prim.Quotient(1, 2), 1: z**2}

# }}}


# {{{ test_np_bool_handling

def test_np_bool_handling():
    from pymbolic.mapper.evaluator import evaluate
    numpy = pytest.importorskip("numpy")
    expr = prim.LogicalNot(numpy.bool_(False))
    assert evaluate(expr) is True

# }}}


# {{{ test_mapper_method_of_parent_class

def test_mapper_method_of_parent_class():
    class SpatialConstant(prim.Variable):
        mapper_method = "map_spatial_constant"

    class MyMapper(IdentityMapper):
        def map_spatial_constant(self, expr):
            return 2*expr

    c = SpatialConstant("k")

    assert MyMapper()(c) == 2*c
    assert IdentityMapper()(c) == c

# }}}


# {{{ test_equality_complexity

@pytest.mark.xfail
def test_equality_complexity():
    # NOTE: https://github.com/inducer/pymbolic/issues/73
    from numpy.random import default_rng

    def construct_intestine_graph(depth=64, seed=0):
        rng = default_rng(seed)
        x = prim.Variable("x")

        for _ in range(depth):
            coeff1, coeff2 = rng.integers(1, 10, 2)
            x = coeff1 * x + coeff2 * x

        return x

    def check_equality():
        graph1 = construct_intestine_graph()
        graph2 = construct_intestine_graph()
        graph3 = construct_intestine_graph(seed=3)

        assert graph1 == graph2
        assert graph2 == graph1
        assert graph1 != graph3
        assert graph2 != graph3

    # NOTE: this should finish in a second!
    import multiprocessing
    p = multiprocessing.Process(target=check_equality)
    p.start()
    p.join(timeout=1)

    is_alive = p.is_alive()
    if p.is_alive():
        p.terminate()

    assert not is_alive

# }}}


# {{{ test_cached_mapper_memoizes

class InCacheVerifier(WalkMapper):
    def __init__(self, cached_mapper, walk_call_functions=True):
        super().__init__()
        self.cached_mapper = cached_mapper
        self.walk_call_functions = walk_call_functions

    def post_visit(self, expr):
        if isinstance(expr, prim.ExpressionNode):
            assert (self.cached_mapper.get_cache_key(expr)
                    in self.cached_mapper._cache)

    def map_call(self, expr):
        if not self.visit(expr):
            return

        if self.walk_call_functions:
            self.rec(expr.function)

        for child in expr.parameters:
            self.rec(child)

        self.post_visit(expr)


def test_cached_mapper_memoizes():
    from testlib import (
        AlwaysFlatteningCachedIdentityMapper,
        AlwaysFlatteningIdentityMapper,
    )
    ntests = 40
    for i in range(ntests):
        expr = generate_random_expression(seed=(5+i))

        # {{{ always flattening identity mapper

        # Note: Prefer AlwaysFlatteningIdentityMapper over IdentityMapper as
        # the flattening logic in IdentityMapper checks for identity across
        # traversal results => leading to discrepancy b/w
        # 'CachedIdentityMapper' and 'IdentityMapper'

        cached_mapper = AlwaysFlatteningCachedIdentityMapper()
        uncached_mapper = AlwaysFlatteningIdentityMapper()
        assert uncached_mapper(expr) == cached_mapper(expr)
        verifier = InCacheVerifier(cached_mapper)
        verifier(expr)

        # }}}

        # {{{ dependency mapper

        mapper = DependencyMapper(include_calls="descend_args")
        cached_mapper = CachedDependencyMapper(include_calls="descend_args")
        assert cached_mapper(expr) == mapper(expr)
        verifier = InCacheVerifier(cached_mapper,
                                   # dep. mapper does not go over functions
                                   walk_call_functions=False
                                   )
        verifier(expr)

        # }}}


def test_cached_mapper_differentiates_float_int():
    # pymbolic.git<=d343cf14 failed this regression.
    from pymbolic.mapper import CachedIdentityMapper
    expr = prim.Sum((4, 4.0))
    cached_mapper = CachedIdentityMapper()
    new_expr = cached_mapper(expr)
    assert isinstance(new_expr.children[0], int)
    assert isinstance(new_expr.children[1], float)

# }}}


# {{{ test_mapper_optimizer

def test_mapper_optimizer():
    from testlib import BIG_EXPR_STR, OptimizedRenamer, Renamer

    from pymbolic.mapper import CachedIdentityMapper

    expr = parse(BIG_EXPR_STR)
    expr = CachedIdentityMapper()(expr)  # remove duplicate nodes

    result_ref = Renamer()(expr)
    result_opt = OptimizedRenamer()(expr)

    assert result_ref == result_opt

# }}}


def test_nodecount():
    from pymbolic.mapper.analysis import get_num_nodes
    expr = prim.Sum((4, 4.0))

    assert get_num_nodes(expr) == 3

    x = prim.Variable("x")
    y = prim.Variable("y")
    z = prim.Variable("z")

    subexpr = prim.make_common_subexpression(4 * (x**2 + y + z))
    expr = 3*subexpr + subexpr + subexpr + subexpr
    expr = expr + expr + expr

    assert get_num_nodes(expr) == 12


def test_python_ast_interop_roundtrip():
    from pymbolic.interop.ast import ASTToPymbolic, PymbolicToASTMapper

    ast2p = ASTToPymbolic()
    p2ast = PymbolicToASTMapper()
    ntests = 40
    for i in range(ntests):
        expr = generate_random_expression(seed=(5+i))
        assert ast2p(p2ast(expr)) == expr


# {{{ test derived stringifiers

@prim.expr_dataclass()
class CustomOperator:
    child: Expression

    def make_stringifier(self, originating_stringifier=None):
        return OperatorStringifier()


class OperatorStringifier(StringifyMapper[[]]):
    def map_custom_operator(self, expr: CustomOperator):
        return f"Op({self.rec(expr.child)})"


def test_derived_stringifier() -> None:
    str(CustomOperator(5))

# }}}


# {{{ test_flatten

class IntegerFlattenMapper(FlattenMapper):
    def is_expr_integer_valued(self, expr: Expression) -> bool:
        return True


def test_flatten():
    expr = parse("(3 + x) % 1")

    assert IntegerFlattenMapper()(expr) != expr
    assert FlattenMapper()(expr) == expr

    assert evaluate_kw(IntegerFlattenMapper()(expr), x=1) == 0
    assert abs(evaluate_kw(FlattenMapper()(expr), x=1.1) - 0.1) < 1e-12

    expr = parse("(3 + x) // 1")

    assert IntegerFlattenMapper()(expr) != expr
    assert FlattenMapper()(expr) == expr

    assert evaluate_kw(IntegerFlattenMapper()(expr), x=1) == 4
    assert abs(evaluate_kw(FlattenMapper()(expr), x=1.1) - 4) < 1e-12

# }}}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        exec(sys.argv[1])
    else:
        from pytest import main
        main([__file__])

# vim: fdm=marker
