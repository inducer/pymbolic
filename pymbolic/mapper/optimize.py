from __future__ import annotations


__copyright__ = "Copyright (C) 2022 University of Illinois Board of Trustees"

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
from collections.abc import Callable, Iterable, MutableMapping
from functools import cached_property, lru_cache
from typing import TextIO, TypeVar, cast


# This machinery applies AST rewriting to the mapper in a mildly brutal
# manner, and as such it requires some attention from the user to
# make sure all transformations applied are valid. A good way to do
# this is to look at the generated code by setting print_modified_code_file
# to sys.stdout or the like.

# Note that this machinery is intentionally generic enough so as to also
# apply to pytato's mappers in unmodified form.


# {{{ ast retrieval

AstDefNodeT = TypeVar("AstDefNodeT", ast.FunctionDef, ast.ClassDef)


def _get_def_from_ast_container(
            container: Iterable[ast.AST],
            name: str,
            node_type: type[AstDefNodeT]
        ) -> AstDefNodeT:
    for entry in container:
        if isinstance(entry, node_type) and entry.name == name:
            return entry

    raise ValueError(f"symbol '{name}' not found")


@lru_cache
def _get_ast_for_file(filename: str) -> ast.Module:
    with open(filename) as inf:
        return ast.parse(inf.read(), filename)


def _get_file_name_for_module_name(module_name: str) -> str | None:
    from importlib import import_module
    return import_module(module_name).__file__


def _get_ast_for_module_name(module_name: str) -> ast.Module:
    return _get_ast_for_file(_get_file_name_for_module_name(module_name))


def _get_module_ast_for_object(obj):
    return _get_ast_for_module_name(obj.__module__)


def _get_ast_for_class(cls: type) -> ast.ClassDef:
    mod_ast = _get_module_ast_for_object(cls)
    return _get_def_from_ast_container(
            mod_ast.body, cls.__name__, ast.ClassDef)


def _get_ast_for_method(f: Callable) -> ast.FunctionDef:
    dot_components = f.__qualname__.split(".")
    assert dot_components[-1] == f.__name__
    cls_name, = dot_components[:-1]
    mod_ast = _get_ast_for_module_name(f.__module__)
    cls_ast = _get_def_from_ast_container(
            mod_ast.body, cls_name, ast.ClassDef)
    return _get_def_from_ast_container(
            cls_ast.body, f.__name__, ast.FunctionDef)

# }}}


def _replace(obj, **kwargs):
    try:
        kwargs["lineno"] = obj.lineno
    except AttributeError:
        pass
    try:
        kwargs["col_offsets"] = obj.col_offsets
    except AttributeError:
        pass

    return type(obj)(**{
        name: kwargs.get(name, getattr(obj, name))
        for name in set(obj._fields) | set(kwargs.keys())
        })


class _VarArgsRemover(ast.NodeTransformer):
    def __init__(self, drop_args, drop_kwargs):
        self.drop_args = drop_args
        self.drop_kwargs = drop_kwargs

    def visit_Call(self, node):  # noqa: N802
        node = self.generic_visit(node)
        return _replace(node,
                       args=[arg for arg in node.args
                          if not self.drop_args or not isinstance(arg, ast.Starred)],
                       keywords=[kw for kw in node.keywords
                          if not self.drop_kwargs or kw.arg is not None])


class _RecInliner(ast.NodeTransformer):
    def __init__(self, *, inline_rec, inline_cache):
        self.inline_rec = inline_rec
        self.inline_cache = inline_cache

    def visit_Call(self, node: ast.Call) -> ast.AST:  # noqa: N802
        node = cast(ast.Call, self.generic_visit(node))

        result_expr: ast.expr = node

        if (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr in ["rec", "rec_arith"]):

            from ast import (
                Attribute,
                Call,
                Compare,
                Constant,
                IfExp,
                IsNot,
                Load,
                Name,
                NamedExpr,
                Store,
            )
            expr = node.args[0]
            self_sym = Name(id="self", ctx=Load())
            fallback_call = _replace(
                    node,
                    func=Attribute(value=self_sym, attr="rec_fallback", ctx=Load()))

            def getattr_sym(obj, name):
                return Call(
                        func=Name(id="getattr", ctx=Load()),
                        args=[obj, name, Constant(value=None)], keywords=[])

            def is_not_none(obj):
                return Compare(
                        left=obj, ops=[IsNot()], comparators=[Constant(value=None)])

            def expr_assign(name, value):
                return NamedExpr(
                        target=Name(id=name, ctx=Store()),
                        value=value)

            if self.inline_rec:
                result_expr = IfExp(
                    test=is_not_none(
                        expr_assign("mname",
                            getattr_sym(expr, Constant(value="mapper_method")))),
                    body=IfExp(
                        test=is_not_none(
                            expr_assign("method", getattr_sym(
                                    self_sym, Name(id="mname", ctx=Load())))),
                        body=_replace(node, func=Name(id="method", ctx=Load())),
                        orelse=fallback_call),
                    orelse=fallback_call)

            if self.inline_cache:
                cache = Attribute(value=self_sym, attr="_cache")
                expr_type = Call(
                        func=Name(id="type", ctx=Load()),
                        args=[expr],
                        keywords=[])
                cache_key_expr = ast.Tuple([expr_type, expr], ctx=Load())
                nic = Name(id="_NotInCache", ctx=Load())

                result_expr = IfExp(
                        test=Compare(
                            left=expr_assign(
                                "result",
                                Call(
                                    func=Attribute(value=cache, attr="get"),
                                    args=[
                                        expr_assign(
                                            "cache_key",
                                            cache_key_expr),
                                        nic
                                        ], keywords=[])),
                                ops=[IsNot()], comparators=[nic]),
                        body=Name(id="result", ctx=Load()),
                        orelse=Call(
                            func=Name(id="_set_and_return", ctx=Load()),
                            args=[cache,
                                    Name(id="cache_key", ctx=Load()),
                                    result_expr], keywords=[]))

        return result_expr


def _get_cache_key_expr(mdef):
    for stmt in mdef.body:
        if isinstance(stmt, ast.Expr):
            # assume no side effects, likely a docstring
            pass
        elif isinstance(stmt, ast.Return):
            return stmt.value
        else:
            raise ValueError("unexpected statement type in get_cache_key: "
                             "{type(stmt).__name__} --- must only contain a single "
                             "return statement")


class _CacheKeyInliner(ast.NodeTransformer):
    def __init__(self, *, cache_key_expr):
        self.cache_key_expr = cache_key_expr

    def visit_Call(self, node):  # noqa: N802
        node = self.generic_visit(node)

        result_expr = node

        if (isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "self"
                and node.func.attr == "get_cache_key"):
            result_expr = self.cache_key_expr

        return result_expr


KeyT = TypeVar("KeyT")
ValueT = TypeVar("ValueT")


def _set_and_return(
            mapping: MutableMapping[KeyT, ValueT],
            key: KeyT,
            value: ValueT
        ) -> ValueT:
    mapping[key] = value
    return value


def optimize_mapper(
        *, drop_args: bool = False, drop_kwargs: bool = False,
        inline_rec: bool = False, inline_cache: bool = False,
        inline_get_cache_key: bool = False,
        print_modified_code_file: TextIO | None = None) -> Callable[[type], type]:
    """
    :param print_modified_code_file: a file-like object to which the modified
        code will be printed, or ``None``.
    """
    # This is a crime, an abomination. But a somewhat effective one.

    def wrapper(cls: type) -> type:
        try:
            # Introduced in Py3.9
            ast.unparse  # noqa: B018
        except AttributeError:
            return cls

        # This also needs Py3.8 for the walrus operators used in inlined rec.

        cls_ast = _get_ast_for_class(cls)

        # {{{ gather relevant method definitions

        method_defs = {}
        other_contents = []

        for entry in cls_ast.body:
            if isinstance(entry, ast.FunctionDef):
                method_defs[entry.name] = entry
            else:
                other_contents.append(entry)

        seen_module_names = set()

        # Yes, this grabs the source for all methods, including those
        # from the base classes, and rewrites them. Otherwise, those methods
        # would still use have *args, **kwargs.
        for name in dir(cls):
            if not name.startswith("__") or name == "__call__":
                method = getattr(cls, name)
                if (not callable(method)
                        or isinstance(method, property | cached_property)):
                    # properties don't have *args, **kwargs
                    continue

                seen_module_names.add(method.__module__)
                method_ast = _get_ast_for_method(method)
                if name != method_ast.name:
                    # This happens for aliases. Make them separate methods.
                    method_ast = _replace(method_ast, name=name)

                method_defs[method_ast.name] = method_ast

        # }}}

        # {{{ get expression for get_cache_key

        cache_key_expr = None
        if inline_get_cache_key and "get_cache_key" in method_defs:
            cache_key_expr = _get_cache_key_expr(method_defs["get_cache_key"])

        if inline_get_cache_key and cache_key_expr is None:
            raise ValueError("could not find expression for cache key")

        # }}}

        # {{{ rewrite method_defs

        new_method_defs = []

        for mname in sorted(method_defs):
            mdef = method_defs[mname]

            mdef = _replace(mdef,
                    args=_replace(mdef.args,
                        vararg=None if drop_args else mdef.args.vararg,
                        kwarg=None if drop_kwargs else mdef.args.kwarg))

            mdef = _VarArgsRemover(
                    drop_args=drop_args, drop_kwargs=drop_kwargs).visit(mdef)

            if cache_key_expr is not None:
                mdef = _CacheKeyInliner(cache_key_expr=cache_key_expr).visit(mdef)

            mdef = _RecInliner(
                    inline_rec=inline_rec, inline_cache=inline_cache).visit(mdef)

            ast.fix_missing_locations(mdef)

            new_method_defs.append(mdef)

        cls_ast = _replace(
                cls_ast,
                # other contents second so method aliases work
                body=new_method_defs + other_contents,
                # FIXME: only remove optimize_mapper from decorators
                decorator_list=[])

        # }}}

        code_str = (
                # Incoming code *may* rely on deferred evaluation of annotations.
                # Since we're not checking whether it does, turn it on just in case.
                "from __future__ import annotations\n"
                + ast.unparse(cls_ast))
        if print_modified_code_file:
            print(code_str, file=print_modified_code_file)

        compile_dict = {
                "_MODULE_SOURCE_CODE": code_str,
                "_set_and_return": _set_and_return,
                }

        # {{{ gather symbols from modules from which methods were collected

        from importlib import import_module
        for mod_name in seen_module_names:
            for name, value in import_module(mod_name).__dict__.items():
                if name.startswith("__"):
                    continue
                if name in compile_dict:
                    if compile_dict[name] is not value:
                        raise ValueError(
                                "symbol disagreement in environment: "
                                f"'{name}', most recently from '{mod_name}'")
                compile_dict[name] = value

        # }}}

        exec(compile(
            code_str,
            f"<'{_get_file_name_for_module_name(cls.__module__)}' "
            "modified by optimize_mapper>",
            "exec"),
             compile_dict)

        return cast(type, compile_dict[cls.__name__])

    return wrapper

# vim: foldmethod=marker
