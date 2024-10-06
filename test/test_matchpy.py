from __future__ import annotations


__copyright__ = "Copyright (C) 2022 Kaushik Kulkarni"

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


import pymbolic.interop.matchpy as m
import pymbolic.primitives as p


def test_replace_with_variadic_op():
    # Replace 'a * c' -> '6'

    from pytools import product

    w1 = p.StarWildcard("w1_star")
    a, b, c = p.variables("a b c")

    def a_times_c_is_6(w1_star):
        result_args = [6]
        for k, v in w1_star.items():
            result_args.extend([k]*v)

        return product(result_args)

    a_times_c_pattern = a * c * w1
    expr = a * b * c

    rule = m.make_replacement_rule(a_times_c_pattern, a_times_c_is_6)
    replaced_expr = m.replace_all(expr, [rule])
    assert replaced_expr == (6 * b)


def test_replace_with_non_commutative_op():
    # Replace 'f(a, b, c, ...)' -> 'g(d, ...)'
    w1 = p.StarWildcard("w1_star")
    a, b, c, d, f, g, x, y, z = p.variables("a b c d f g x y z")

    def replacer(w1_star):
        return g(d, *w1_star)

    rule = m.make_replacement_rule(f(a, b, c, w1), replacer)
    replaced_expr = m.replace_all(f(a, b, c, x, y, z), [rule])
    assert replaced_expr == g(d, x, y, z)


def test_replace_with_ternary_ops():
    from pymbolic import parse

    expr = parse("b < f(c, d)")
    rule = m.make_replacement_rule(
        p.Variable("f")(p.Variable("c"), p.DotWildcard("w1_")),
        lambda w1_: (w1_*42))
    assert m.replace_all(expr, [rule]) == parse("b < (42 * d)")

    expr = parse("b if f(c, d) else g(e)")
    rule = m.make_replacement_rule(
        p.If(parse("f(c, d)"),
             p.DotWildcard("w1_"),
             p.DotWildcard("w2_")),
        lambda w1_, w2_: p.If(parse("f(d, c)"), w2_, w1_))
    assert m.replace_all(expr, [rule]) == parse("g(e) if f(d, c) else b")


def test_make_subexpr_subst():
    from functools import reduce

    from pymbolic import parse
    from pymbolic.mapper.flattener import flatten

    subject = parse("a[k]*b[i, j]*c[i, j]*d[k]")
    pattern = parse("b[i, j]*c[i, j]") * p.StarWildcard("w1_")

    rule = m.make_replacement_rule(
        pattern,
        lambda w1_: (parse("subst(i, j)")
                     * (reduce(lambda acc, x: acc * (x[0] ** x[1]),
                               w1_.items(),
                               1)))
    )

    replaced_expr = m.replace_all(subject, [rule])

    ref_expr = flatten(parse("subst(i, j)*a[(k,)]*d[(k,)]"))
    assert flatten(replaced_expr) == ref_expr
