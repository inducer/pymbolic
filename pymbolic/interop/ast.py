from __future__ import division, absolute_import, print_function

__copyright__ = "Copyright (C) 2015 Andreas Kloeckner"

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

import ast
import pymbolic.primitives as p

__doc__ = r'''

An example::

    src = """
    def f():
        xx = 3*y + z * (12 if x < 13 else 13)
        yy = f(x, y=y)
    """

    import ast
    mod = ast.parse(src.replace("\n    ", "\n"))

    print(ast.dump(mod))

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

            print(lhs, rhs)

.. autoclass:: ASTToPymbolic
'''


class ASTMapper(object):
    def __call__(self, expr, *args, **kwargs):
        return self.rec(expr, *args, **kwargs)

    def rec(self, expr, *args, **kwargs):
        mro = list(type(expr).__mro__)
        dispatch_class = kwargs.pop("dispatch_class", type(self))

        while mro:
            method_name = "map_"+mro.pop(0).__name__

            try:
                method = getattr(dispatch_class, method_name)
            except AttributeError:
                pass
            else:
                return method(self, expr, *args, **kwargs)

        return self.not_supported(expr)

    def not_supported(self, expr):
        raise NotImplementedError(
                "%s does not know how to map type '%s'"
                % (type(self).__name__,
                    type(expr).__name__))


# {{{ mapper

class ASTToPymbolic(ASTMapper):
    def _add(x, y):
        return p.Sum((x, y))

    def _sub(x, y):
        return p.Sum((x, p.Product(((-1), y))))

    def _mult(x, y):
        return p.Product((x, y))

    bin_op_map = {
            ast.Add: _add,
            ast.Sub: _sub,
            ast.Mult: _mult,
            # MatMult
            ast.Div: p.Quotient,
            ast.FloorDiv: p.FloorDiv,
            ast.Mod: p.Remainder,
            ast.Pow: p.Power,
            ast.LShift: p.LeftShift,
            ast.RShift: p.RightShift,
            ast.BitOr: p.BitwiseOr,
            ast.BitXor: p.BitwiseXor,
            ast.BitAnd: p.BitwiseAnd,
            }

    def map_BinOp(self, expr):
        try:
            op_constructor = self.bin_op_map[type(expr.op)]
        except KeyError:
            raise NotImplementedError(
                    "%s does not know how to map operator '%s'"
                    % (type(self).__name__,
                        type(expr.op).__name__))

        return op_constructor(self.rec(expr.left), self.rec(expr.right))

    def _neg(x):
        return p.Product((-1), x)

    unary_op_map = {
            ast.Invert: _neg,
            ast.Not: p.LogicalNot,
            # ast.UAdd:
            ast.USub: _neg,
            }

    def map_UnaryOp(self, expr):
        try:
            op_constructor = self.unary_op_map[expr.op]
        except KeyError:
            raise NotImplementedError(
                    "%s does not know how to map operator '%s'"
                    % (type(self).__name__,
                        type(expr.op).__name__))

        return op_constructor(self.rec(expr.left), self.rec(expr.right))

    def map_IfExp(self, expr):
        # (expr test, expr body, expr orelse)
        return p.If(self.rec(expr.test), self.rec(expr.body), self.rec(expr.orelse))

    comparison_op_map = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            # Is
            # IsNot
            # In
            # NotIn
            }

    def map_Compare(self, expr):
        # (expr left, cmpop* ops, expr* comparators)
        op, = expr.ops

        try:
            comp = self.comparison_op_map[type(op)]
        except KeyError:
            raise NotImplementedError(
                    "%s does not know how to map operator '%s'"
                    % (type(self).__name__,
                        type(op).__name__))

        # FIXME: Support strung-together comparisons
        right, = expr.comparators

        return p.Comparison(self.rec(expr.left), comp, self.rec(right))

    def map_Call(self, expr):
        # (expr func, expr* args, keyword* keywords)
        func = self.rec(expr.func)
        args = tuple(self.rec(arg) for arg in expr.args)
        if expr.keywords:
            return p.CallWithKwargs(func, args,
                    dict(
                        (kw.arg, self.rec(kw.value))
                        for kw in expr.keywords))
        else:
            return p.Call(func, args)

    def map_Num(self, expr):
        # (object n) -- a number as a PyObject.
        return expr.n

    def map_Str(self, expr):
        return expr.s

    def map_Bytes(self, expr):
        return expr.s

    def map_NameConstant(self, expr):
        # (singleton value)
        return expr.value

    def map_Attribute(self, expr):
        # (expr value, identifier attr, expr_context ctx)
        return p.Lookup(self.rec(expr.value), expr.attr)

    def map_Subscript(self, expr):
        # (expr value, slice slice, expr_context ctx)
        def none_or_rec(x):
            if x is None:
                return x
            else:
                return self.rec(x)

        if isinstance(expr.slice, slice):
            index = slice(
                    none_or_rec(expr.slice.start),
                    none_or_rec(expr.slice.stop),
                    none_or_rec(expr.slice.step))
        else:
            index = none_or_rec(expr.slice)

        return p.Subscript(
                self.rec(expr.value),
                index)

    # def map_Starred(self, expr):

    def map_Name(self, expr):
        # (identifier id, expr_context ctx)
        return p.Variable(expr.id)

    def map_Tuple(self, expr):
        # (expr* elts, expr_context ctx)
        return tuple(self.rec(ti) for ti in expr.elts)

# }}}

# vim: foldmethod=marker
