__copyright__ = """
Copyright (C) 2015 Andreas Kloeckner
Copyright (C) 2022 Kaushik Kulkarni
"""

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
from typing import Tuple, List, Any
from pymbolic.typing import ExpressionT, ScalarT
from pymbolic.mapper import CachedMapper

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


class ASTMapper:
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
                "{} does not know how to map type '{}'".format(
                    type(self).__name__,
                    type(expr).__name__))


# {{{ mapper

def _add(x, y):
    return p.Sum((x, y))


def _sub(x, y):
    return p.Sum((x, p.Product(((-1), y))))


def _mult(x, y):
    return p.Product((x, y))


def _neg(x):
    return -x


class ASTToPymbolic(ASTMapper):

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

    def map_BinOp(self, expr):  # noqa
        try:
            op_constructor = self.bin_op_map[type(expr.op)]
        except KeyError:
            raise NotImplementedError(
                    "{} does not know how to map operator '{}'".format(
                        type(self).__name__,
                        type(expr.op).__name__))

        return op_constructor(self.rec(expr.left), self.rec(expr.right))

    unary_op_map = {
            ast.Invert: _neg,
            ast.Not: p.LogicalNot,
            # ast.UAdd:
            ast.USub: _neg,
            }

    def map_UnaryOp(self, expr):  # noqa
        try:
            op_constructor = self.unary_op_map[type(expr.op)]
        except KeyError:
            raise NotImplementedError(
                    "{} does not know how to map operator '{}'".format(
                        type(self).__name__,
                        type(expr.op).__name__))

        return op_constructor(self.rec(expr.operand))

    def map_IfExp(self, expr):  # noqa
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

    def map_Compare(self, expr):  # noqa
        # (expr left, cmpop* ops, expr* comparators)
        op, = expr.ops

        try:
            comp = self.comparison_op_map[type(op)]
        except KeyError:
            raise NotImplementedError(
                    "{} does not know how to map operator '{}'".format(
                        type(self).__name__,
                        type(op).__name__))

        # FIXME: Support strung-together comparisons
        right, = expr.comparators

        return p.Comparison(self.rec(expr.left), comp, self.rec(right))

    def map_Call(self, expr):  # noqa
        # (expr func, expr* args, keyword* keywords)
        func = self.rec(expr.func)
        args = tuple([self.rec(arg) for arg in expr.args])
        if getattr(expr, "keywords", []):
            return p.CallWithKwargs(func, args,
                    {
                        kw.arg: self.rec(kw.value)
                        for kw in expr.keywords})
        else:
            return p.Call(func, args)

    def map_Num(self, expr):  # noqa
        # (object n) -- a number as a PyObject.
        return expr.n

    def map_Str(self, expr):  # noqa
        return expr.s

    def map_Bytes(self, expr):  # noqa
        return expr.s

    # 3.8 and up
    def map_Constant(self, expr):  # noqa
        # (singleton value)
        return expr.value

    def map_NameConstant(self, expr):  # noqa
        # (singleton value)
        return expr.value

    def map_Attribute(self, expr):  # noqa
        # (expr value, identifier attr, expr_context ctx)
        return p.Lookup(self.rec(expr.value), expr.attr)

    def map_Subscript(self, expr):  # noqa
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

    def map_Name(self, expr):  # noqa
        # (identifier id, expr_context ctx)
        return p.Variable(expr.id)

    def map_Tuple(self, expr):  # noqa
        # (expr* elts, expr_context ctx)
        return tuple([self.rec(ti) for ti in expr.elts])

# }}}


# {{{ PymbolicToASTMapper

class PymbolicToASTMapper(CachedMapper):
    def map_variable(self, expr) -> ast.expr:
        return ast.Name(id=expr.name)

    def _map_multi_children_op(self,
                               children: Tuple[ExpressionT, ...],
                               op_type: ast.operator) -> ast.expr:
        rec_children = [self.rec(child) for child in children]
        result = rec_children[-1]
        for child in rec_children[-2::-1]:
            result = ast.BinOp(child, op_type, result)

        return result

    def map_sum(self, expr: p.Sum) -> ast.expr:
        return self._map_multi_children_op(expr.children, ast.Add())

    def map_product(self, expr: p.Product) -> ast.expr:
        return self._map_multi_children_op(expr.children, ast.Mult())

    def map_constant(self, expr: ScalarT) -> ast.expr:
        import sys
        if isinstance(expr, bool):
            return ast.NameConstant(expr)
        else:
            # needed because of https://bugs.python.org/issue36280
            if sys.version_info < (3, 8):
                return ast.Num(expr)
            else:
                return ast.Constant(expr, None)

    def map_call(self, expr: p.Call) -> ast.expr:
        return ast.Call(
            func=self.rec(expr.function),
            args=[self.rec(param) for param in expr.parameters])

    def map_call_with_kwargs(self, expr) -> ast.expr:
        return ast.Call(
            func=self.rec(expr.function),
            args=[self.rec(param) for param in expr.parameters],
            keywords=[
                ast.keyword(
                    arg=kw,
                    value=self.rec(param))
                for kw, param in sorted(expr.kw_parameters.items())])

    def map_subscript(self, expr) -> ast.expr:
        return ast.Subscript(value=self.rec(expr.aggregate),
                             slice=self.rec(expr.index))

    def map_lookup(self, expr) -> ast.expr:
        return ast.Attribute(self.rec(expr.aggregate),
                             expr.name)

    def map_quotient(self, expr) -> ast.expr:
        return self._map_multi_children_op((expr.numerator,
                                            expr.denominator),
                                           ast.Div())

    def map_floor_div(self, expr) -> ast.expr:
        return self._map_multi_children_op((expr.numerator,
                                            expr.denominator),
                                           ast.FloorDiv())

    def map_remainder(self, expr) -> ast.expr:
        return self._map_multi_children_op((expr.numerator,
                                            expr.denominator),
                                           ast.Mod())

    def map_power(self, expr) -> ast.expr:
        return self._map_multi_children_op((expr.base,
                                            expr.exponent),
                                           ast.Pow())

    def map_left_shift(self, expr) -> ast.expr:
        return self._map_multi_children_op((expr.shiftee,
                                            expr.shift),
                                           ast.LShift())

    def map_right_shift(self, expr) -> ast.expr:
        return self._map_multi_children_op((expr.numerator,
                                            expr.denominator),
                                           ast.RShift())

    def map_bitwise_not(self, expr) -> ast.expr:
        return ast.UnaryOp(ast.Invert(), self.rec(expr.child))

    def map_bitwise_or(self, expr) -> ast.expr:
        return self._map_multi_children_op(expr.children,
                                           ast.BitOr())

    def map_bitwise_xor(self, expr) -> ast.expr:
        return self._map_multi_children_op(expr.children,
                                           ast.BitXor())

    def map_bitwise_and(self, expr) -> ast.expr:
        return self._map_multi_children_op(expr.children,
                                           ast.BitAnd())

    def map_logical_not(self, expr) -> ast.expr:
        return ast.UnaryOp(self.rec(expr.child), ast.Not())

    def map_logical_or(self, expr) -> ast.expr:
        return ast.BoolOp(ast.Or(), [self.rec(child)
                                     for child in expr.children])

    def map_logical_and(self, expr) -> ast.expr:
        return ast.BoolOp(ast.And(), [self.rec(child)
                                     for child in expr.children])

    def map_list(self, expr: List[Any]) -> ast.expr:
        return ast.List([self.rec(el) for el in expr])

    def map_tuple(self, expr: Tuple[Any, ...]) -> ast.expr:
        return ast.Tuple([self.rec(el) for el in expr])

    def map_if(self, expr: p.If) -> ast.expr:
        return ast.IfExp(test=self.rec(expr.condition),
                         body=self.rec(expr.then),
                         orelse=self.rec(expr.else_))

    def map_nan(self, expr: p.NaN) -> ast.expr:
        if isinstance(expr.data_type(float("nan")), float):
            return ast.Call(
                ast.Name(id="float"),
                args=[ast.Constant("nan")],
                keywords=[])
        else:
            # TODO: would need attributes of NumPy
            raise NotImplementedError("Non-float nan not implemented")

    def map_slice(self, expr: p.Slice) -> ast.expr:
        return ast.Slice(*[self.rec(child)
                           for child in expr.children])

    def map_numpy_array(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_multivector(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_common_subexpression(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_substitution(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_derivative(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_if_positive(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_comparison(self, expr: p.Comparison) -> ast.expr:
        raise NotImplementedError

    def map_polynomial(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_wildcard(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_dot_wildcard(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_star_wildcard(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_function_symbol(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_min(self, expr) -> ast.expr:
        raise NotImplementedError

    def map_max(self, expr) -> ast.expr:
        raise NotImplementedError


def to_python_ast(expr) -> ast.expr:
    """
    Maps *expr* to :class:`ast.expr`.
    """
    return PymbolicToASTMapper()(expr)


def to_evaluatable_python_function(expr: ExpressionT,
                                   fn_name: str
                                   ) -> str:
    """
    Returns a :class:`str` of the python code with a single function *fn_name*
    that takes in the variables in *expr* as keyword-only arguments and returns
    the evaluated value of *expr*.

    .. testsetup::

        >>> from pymbolic import parse
        >>> from pymbolic.interop.ast import to_evaluatable_python_function

    .. doctest::

        >>> expr = parse("S//32 + E%32")
        >>> # Skipping doctest as astunparse and ast.unparse have certain subtle
        >>> # differences
        >>> print(to_evaluatable_python_function(expr, "foo"))) # doctest: +SKIP
        def foo(*, E, S):
            return S // 32 + E % 32
    """
    import sys
    from pymbolic.mapper.dependency import CachedDependencyMapper

    if sys.version_info < (3, 9):
        try:
            from astunparse import unparse
        except ImportError:
            raise RuntimeError("'to_evaluate_python_function' needs"
                               "astunparse for Py<3.9. Install via `pip"
                               " install astunparse`")
    else:
        unparse = ast.unparse

    dep_mapper = CachedDependencyMapper(composite_leaves=True)
    deps = sorted({dep.name for dep in dep_mapper(expr)})

    ast_func = ast.FunctionDef(name=fn_name,
                               args=ast.arguments(args=[],
                                                  posonlyargs=[],
                                                  kwonlyargs=[ast.arg(dep, None)
                                                              for dep in deps],
                                                  kw_defaults=[None]*len(deps),
                                                  vararg=None,
                                                  kwarg=None,
                                                  defaults=[]),
                               body=[ast.Return(to_python_ast(expr))],
                               decorator_list=[])
    ast_module = ast.Module([ast_func], type_ignores=[])

    return unparse(ast.fix_missing_locations(ast_module))

# }}}

# vim: foldmethod=marker
