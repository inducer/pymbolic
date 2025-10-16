from __future__ import annotations


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
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeAlias

from constantdict import constantdict
from typing_extensions import override

import pymbolic.primitives as p
from pymbolic.mapper import CachedMapper, P, ResultT
from pymbolic.typing import ArithmeticExpression, Expression


if TYPE_CHECKING:
    import sys
    from collections.abc import Callable

    from numpy.typing import NDArray

    from pymbolic.geometric_algebra import MultiVector

    # NOTE: these are removed in Python 3.14
    if sys.version_info < (3, 14):
        from ast import (
            Bytes as AstBytes,  # pyright: ignore[reportDeprecated]
            Num as AstNum,  # pyright: ignore[reportDeprecated]
            Str as AstStr,  # pyright: ignore[reportDeprecated]
        )
    else:
        AstNum: TypeAlias = Any
        AstStr: TypeAlias = Any
        AstBytes: TypeAlias = Any

__doc__ = r'''
An example:

.. code:: python

    import ast

    from pymbolic.interop.ast import ASTToPymbolic


    src = """
    def f():
        xx = 3*y + z * (12 if x < 13 else 13)
        yy = f(x, y=y)
    """

    mod = ast.parse(src.replace("\n    ", "\n"))
    print(ast.dump(mod))

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
.. autoclass:: PymbolicToASTMapper
.. autofunction:: to_python_ast
.. autofunction:: to_evaluatable_python_function
'''


class ASTMapper(Generic[ResultT, P]):
    def __call__(self, expr: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        return self.rec(expr, *args, **kwargs)

    def rec(self, expr: object, *args: P.args, **kwargs: P.kwargs) -> ResultT:
        mro = list(type(expr).__mro__)
        dispatch_class = kwargs.pop("dispatch_class", type(self))

        while mro:
            method_name = f"map_{mro[0].__name__}"
            mro.pop(0)

            method = getattr(dispatch_class, method_name, None)
            if method is not None:
                return method(self, expr, *args, **kwargs)

        return self.not_supported(expr)

    def not_supported(self, expr: object) -> ResultT:
        raise NotImplementedError(
                f"{type(self)} does not know how to map type {type(expr)}")


# {{{ mapper

def _add(x: ArithmeticExpression, y: ArithmeticExpression) -> ArithmeticExpression:
    return p.Sum((x, y))


def _sub(x: ArithmeticExpression, y: ArithmeticExpression) -> ArithmeticExpression:
    return p.Sum((x, p.Product(((-1), y))))


def _mult(x: ArithmeticExpression, y: ArithmeticExpression) -> ArithmeticExpression:
    return p.Product((x, y))


def _neg(x: ArithmeticExpression) -> ArithmeticExpression:
    return -x


class ASTToPymbolic(ASTMapper[Expression, []]):
    """
    .. automethod:: __call__
    """

    bin_op_map: ClassVar[
        dict[type[ast.operator], Callable[..., ArithmeticExpression]]] = {
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

    def map_BinOp(self, expr: ast.BinOp) -> Expression:
        try:
            op_constructor = self.bin_op_map[type(expr.op)]
        except KeyError:
            raise NotImplementedError(
                f"{type(self)} does not know how to map operator "
                f"{type(expr.op)}") from None

        return op_constructor(self.rec(expr.left), self.rec(expr.right))

    unary_op_map: ClassVar[
        dict[type[ast.unaryop], Callable[..., ArithmeticExpression]]] = {
            ast.Invert: _neg,
            ast.Not: p.LogicalNot,
            # ast.UAdd:
            ast.USub: _neg,
        }

    def map_UnaryOp(self, expr: ast.UnaryOp) -> Expression:
        try:
            op_constructor = self.unary_op_map[type(expr.op)]
        except KeyError:
            raise NotImplementedError(
                f"{type(self)} does not know how to map operator "
                f"{type(expr.op)}") from None

        return op_constructor(self.rec(expr.operand))

    def map_IfExp(self, expr: ast.IfExp) -> Expression:
        # (expr test, expr body, expr orelse)
        return p.If(self.rec(expr.test), self.rec(expr.body), self.rec(expr.orelse))

    comparison_op_map: ClassVar[dict[type[ast.cmpop], str]] = {
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

    def map_Compare(self, expr: ast.Compare) -> Expression:
        # (expr left, cmpop* ops, expr* comparators)
        op, = expr.ops

        try:
            comp = self.comparison_op_map[type(op)]
        except KeyError:
            raise NotImplementedError(
                f"{type(self)} does not know how to map operator {op}") from None

        # FIXME: Support strung-together comparisons
        right, = expr.comparators

        return p.Comparison(self.rec(expr.left), comp, self.rec(right))

    def map_Call(self, expr: ast.Call) -> Expression:
        # (expr func, expr* args, keyword* keywords)
        func = self.rec(expr.func)
        args = tuple([self.rec(arg) for arg in expr.args])
        if getattr(expr, "keywords", []):
            return p.CallWithKwargs(
                func,
                args,
                constantdict({kw.arg: self.rec(kw.value) for kw in expr.keywords}))
        else:
            return p.Call(func, args)

    # {{{ removed in Python 3.14

    def map_Num(self, expr: AstNum) -> Expression:
        # (object n) -- a number as a PyObject.
        return expr.n

    def map_Str(self, expr: AstStr) -> Expression:
        return expr.s

    def map_Bytes(self, expr: AstBytes) -> Expression:
        return expr.s

    # }}}

    def map_Constant(self, expr: ast.Constant) -> Expression:
        # (singleton value)
        return expr.value

    def map_Attribute(self, expr: ast.Attribute) -> Expression:
        # (expr value, identifier attr, expr_context ctx)
        return p.Lookup(self.rec(expr.value), expr.attr)

    def map_Subscript(self, expr: ast.Subscript) -> Expression:
        # (expr value, slice slice, expr_context ctx)
        def none_or_rec(x: object) -> Expression | None:
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

        return p.Subscript(self.rec(expr.value), index)

    # def map_Starred(self, expr):

    def map_Name(self, expr: ast.Name) -> Expression:
        # (identifier id, expr_context ctx)
        return p.Variable(expr.id)

    def map_Tuple(self, expr: ast.Tuple) -> Expression:
        # (expr* elts, expr_context ctx)
        return tuple([self.rec(ti) for ti in expr.elts])

# }}}


# {{{ PymbolicToASTMapper

class PymbolicToASTMapper(CachedMapper[ast.expr, []]):
    """
    .. automethod:: __call__
    """

    @override
    def map_variable(self, expr: p.Variable) -> ast.expr:
        return ast.Name(id=expr.name)

    def _map_multi_children_op(self,
                               children: tuple[Expression, ...],
                               op_type: ast.operator) -> ast.expr:
        rec_children = [self.rec(child) for child in children]
        result = rec_children[-1]
        for child in rec_children[-2::-1]:
            result = ast.BinOp(child, op_type, result)

        return result

    @override
    def map_sum(self, expr: p.Sum) -> ast.expr:
        return self._map_multi_children_op(expr.children, ast.Add())

    @override
    def map_product(self, expr: p.Product) -> ast.expr:
        return self._map_multi_children_op(expr.children, ast.Mult())

    @override
    def map_constant(self, expr: object) -> ast.expr:
        return ast.Constant(expr, None)  # pyright: ignore[reportArgumentType]

    @override
    def map_call(self, expr: p.Call) -> ast.expr:
        return ast.Call(
            func=self.rec(expr.function),
            args=[self.rec(param) for param in expr.parameters],
            keywords=[],
        )

    @override
    def map_call_with_kwargs(self, expr: p.CallWithKwargs) -> ast.expr:
        return ast.Call(
            func=self.rec(expr.function),
            args=[self.rec(param) for param in expr.parameters],
            keywords=[
                ast.keyword(
                    arg=kw,
                    value=self.rec(param))
                for kw, param in sorted(expr.kw_parameters.items())])

    @override
    def map_subscript(self, expr: p.Subscript) -> ast.expr:
        return ast.Subscript(value=self.rec(expr.aggregate),
                             slice=self.rec(expr.index))

    @override
    def map_lookup(self, expr: p.Lookup) -> ast.expr:
        return ast.Attribute(self.rec(expr.aggregate),
                             expr.name)

    @override
    def map_quotient(self, expr: p.Quotient) -> ast.expr:
        return self._map_multi_children_op((expr.numerator, expr.denominator),
                                           ast.Div())

    @override
    def map_floor_div(self, expr: p.FloorDiv) -> ast.expr:
        return self._map_multi_children_op((expr.numerator, expr.denominator),
                                           ast.FloorDiv())

    @override
    def map_remainder(self, expr: p.Remainder) -> ast.expr:
        return self._map_multi_children_op((expr.numerator, expr.denominator),
                                           ast.Mod())

    @override
    def map_power(self, expr: p.Power) -> ast.expr:
        return self._map_multi_children_op((expr.base, expr.exponent),
                                           ast.Pow())

    @override
    def map_left_shift(self, expr: p.LeftShift) -> ast.expr:
        return self._map_multi_children_op((expr.shiftee, expr.shift),
                                           ast.LShift())

    @override
    def map_right_shift(self, expr: p.RightShift) -> ast.expr:
        return self._map_multi_children_op((expr.shiftee, expr.shift),
                                           ast.RShift())

    @override
    def map_bitwise_not(self, expr: p.BitwiseNot) -> ast.expr:
        return ast.UnaryOp(ast.Invert(), self.rec(expr.child))

    @override
    def map_bitwise_or(self, expr: p.BitwiseOr) -> ast.expr:
        return self._map_multi_children_op(expr.children,
                                           ast.BitOr())

    @override
    def map_bitwise_xor(self, expr: p.BitwiseXor) -> ast.expr:
        return self._map_multi_children_op(expr.children,
                                           ast.BitXor())

    @override
    def map_bitwise_and(self, expr: p.BitwiseAnd) -> ast.expr:
        return self._map_multi_children_op(expr.children,
                                           ast.BitAnd())

    @override
    def map_logical_not(self, expr: p.LogicalNot) -> ast.expr:
        return ast.UnaryOp(ast.Not(), self.rec(expr.child))

    @override
    def map_logical_or(self, expr: p.LogicalOr) -> ast.expr:
        return ast.BoolOp(ast.Or(), [self.rec(child)
                                     for child in expr.children])

    @override
    def map_logical_and(self, expr: p.LogicalAnd) -> ast.expr:
        return ast.BoolOp(ast.And(), [self.rec(child)
                                     for child in expr.children])

    @override
    def map_list(self, expr: list[Expression]) -> ast.expr:
        return ast.List([self.rec(el) for el in expr])

    @override
    def map_tuple(self, expr: tuple[Expression, ...]) -> ast.expr:
        return ast.Tuple([self.rec(el) for el in expr])

    @override
    def map_if(self, expr: p.If) -> ast.expr:
        return ast.IfExp(test=self.rec(expr.condition),
                         body=self.rec(expr.then),
                         orelse=self.rec(expr.else_))

    @override
    def map_nan(self, expr: p.NaN) -> ast.expr:
        assert expr.data_type is not None
        if isinstance(expr.data_type(float("nan")), float):
            return ast.Call(
                ast.Name(id="float"),
                args=[ast.Constant("nan")],
                keywords=[])
        else:
            # TODO: would need attributes of NumPy
            raise NotImplementedError("Non-float nan not implemented")

    @override
    def map_slice(self, expr: p.Slice) -> ast.expr:
        return ast.Slice(*[None if child is None else self.rec(child)
                           for child in expr.children])

    @override
    def map_numpy_array(self, expr: NDArray[Any]) -> ast.expr:
        raise NotImplementedError

    @override
    def map_multivector(self, expr: MultiVector[Any]) -> ast.expr:
        raise NotImplementedError

    def map_common_subexpression(self, expr: p.CommonSubexpression) -> ast.expr:
        raise NotImplementedError

    @override
    def map_substitution(self, expr: p.Substitution) -> ast.expr:
        raise NotImplementedError

    @override
    def map_derivative(self, expr: p.Derivative) -> ast.expr:
        raise NotImplementedError

    @override
    def map_comparison(self, expr: p.Comparison) -> ast.expr:
        raise NotImplementedError

    @override
    def map_wildcard(self, expr: p.Wildcard) -> ast.expr:
        raise NotImplementedError

    @override
    def map_dot_wildcard(self, expr: p.DotWildcard) -> ast.expr:
        raise NotImplementedError

    @override
    def map_star_wildcard(self, expr: p.StarWildcard) -> ast.expr:
        raise NotImplementedError

    @override
    def map_function_symbol(self, expr: p.FunctionSymbol) -> ast.expr:
        raise NotImplementedError

    @override
    def map_min(self, expr: p.Min) -> ast.expr:
        raise NotImplementedError

    @override
    def map_max(self, expr: p.Max) -> ast.expr:
        raise NotImplementedError


def to_python_ast(expr: Expression) -> ast.expr:
    """
    Maps *expr* to :class:`ast.expr`.
    """
    return PymbolicToASTMapper()(expr)


def to_evaluatable_python_function(expr: Expression, fn_name: str) -> str:
    """
    Returns a :class:`str` of the Python code with a single function *fn_name*
    that takes in the variables in *expr* as keyword-only arguments and returns
    the evaluated value of *expr*.

    .. testsetup::

        >>> from pymbolic import parse
        >>> from pymbolic.interop.ast import to_evaluatable_python_function

    .. doctest::

        >>> expr = parse("S//32 + E%32")
        >>> print(to_evaluatable_python_function(expr, "foo"))
        def foo(*, E, S):
            return S // 32 + E % 32
    """

    from pymbolic.mapper.dependency import CachedDependencyMapper

    dep_mapper: CachedDependencyMapper[[]] = (
        CachedDependencyMapper(composite_leaves=True))

    deps: list[str] = []
    for dep in dep_mapper(expr):
        if isinstance(dep, p.Variable):
            deps.append(dep.name)
        else:
            raise NotImplementedError(f"{dep!r} is not supported")

    ast_func = ast.FunctionDef(name=fn_name,
                               args=ast.arguments(args=[],
                                                  posonlyargs=[],
                                                  kwonlyargs=[ast.arg(dep, None)
                                                              for dep in sorted(deps)],
                                                  kw_defaults=[None]*len(deps),
                                                  vararg=None,
                                                  kwarg=None,
                                                  defaults=[]),
                               body=[ast.Return(to_python_ast(expr))],
                               decorator_list=[])
    ast_module = ast.Module([ast_func], type_ignores=[])

    return ast.unparse(ast.fix_missing_locations(ast_module))

# }}}

# vim: foldmethod=marker
