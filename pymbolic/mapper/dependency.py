"""
.. autoclass:: DependencyMapper
.. autoclass:: CachedDependencyMapper
"""

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

from collections.abc import Set
from typing import TYPE_CHECKING, Literal, TypeAlias

from typing_extensions import override

import pymbolic.primitives as p
from pymbolic.mapper import CachedMapper, Collector, CSECachingMapperMixin, P


Dependency: TypeAlias = p.AlgebraicLeaf | p.CommonSubexpression
Dependencies: TypeAlias = Set[Dependency]

if not TYPE_CHECKING:
    DependenciesT: TypeAlias = Dependencies


class DependencyMapper(
    CSECachingMapperMixin[Dependencies, P],
    Collector[p.AlgebraicLeaf | p.CommonSubexpression, P],
):
    """Maps an expression to the :class:`set` of expressions it
    is based on. The ``include_*`` arguments to the constructor
    determine which types of objects occur in this output set.
    If all are *False*, only :class:`pymbolic.primitives.Variable`
    instances are included.
    """

    def __init__(
        self,
        include_subscripts: bool = True,
        include_lookups: bool = True,
        include_calls: bool | Literal["descend_args"] = True,
        include_cses: bool = False,
        composite_leaves: bool | None = None,
    ) -> None:
        """
        :arg composite_leaves: Setting this is equivalent to setting
            all preceding ``include_*`` flags.
        """

        if composite_leaves is False:
            include_subscripts = False
            include_lookups = False
            include_calls = False

        if composite_leaves is True:
            include_subscripts = True
            include_lookups = True
            include_calls = True

        assert include_calls in [True, False, "descend_args"]

        self.include_subscripts = include_subscripts
        self.include_lookups = include_lookups
        self.include_calls = include_calls
        self.include_cses = include_cses

    @override
    def map_variable(
        self, expr: p.Variable, *args: P.args, **kwargs: P.kwargs
    ) -> Dependencies:
        return {expr}

    @override
    def map_call(
        self, expr: p.Call, *args: P.args, **kwargs: P.kwargs
    ) -> Dependencies:
        if self.include_calls == "descend_args":
            return self.combine([
                self.rec(child, *args, **kwargs) for child in expr.parameters
            ])
        elif self.include_calls:
            return {expr}
        else:
            return super().map_call(expr, *args, **kwargs)

    @override
    def map_call_with_kwargs(
        self, expr: p.CallWithKwargs, *args: P.args, **kwargs: P.kwargs
    ) -> Dependencies:
        if self.include_calls == "descend_args":
            return self.combine(
                [self.rec(child, *args, **kwargs) for child in expr.parameters]
                + [
                    self.rec(val, *args, **kwargs)
                    for name, val in expr.kw_parameters.items()
                ]
            )
        elif self.include_calls:
            return {expr}
        else:
            return super().map_call_with_kwargs(expr, *args, **kwargs)

    @override
    def map_lookup(
        self, expr: p.Lookup, *args: P.args, **kwargs: P.kwargs
    ) -> Dependencies:
        if self.include_lookups:
            return {expr}
        else:
            return super().map_lookup(expr, *args, **kwargs)

    @override
    def map_subscript(
        self, expr: p.Subscript, *args: P.args, **kwargs: P.kwargs
    ) -> Dependencies:
        if self.include_subscripts:
            return {expr}
        else:
            return super().map_subscript(expr, *args, **kwargs)

    @override
    def map_common_subexpression_uncached(
        self, expr: p.CommonSubexpression, *args: P.args, **kwargs: P.kwargs
    ) -> Dependencies:
        if self.include_cses:
            return {expr}
        else:
            # FIXME: These look like mypy bugs, revisit
            return Collector.map_common_subexpression(self, expr, *args, **kwargs)  # type: ignore[return-value, arg-type]

    @override
    def map_slice(
        self, expr: p.Slice, *args: P.args, **kwargs: P.kwargs
    ) -> Dependencies:
        return self.combine([
            self.rec(child, *args, **kwargs)
            for child in expr.children
            if child is not None
        ])

    @override
    def map_nan(self, expr: p.NaN, *args: P.args, **kwargs: P.kwargs) -> Dependencies:
        return set()


class CachedDependencyMapper(CachedMapper[Dependencies, P],
                             DependencyMapper[P]):
    def __init__(
        self,
        include_subscripts: bool = True,
        include_lookups: bool = True,
        include_calls: bool | Literal["descend_args"] = True,
        include_cses: bool = False,
        composite_leaves: bool | None = None,
    ) -> None:
        CachedMapper.__init__(self)
        DependencyMapper.__init__(
            self,
            include_subscripts=include_subscripts,
            include_lookups=include_lookups,
            include_calls=include_calls,
            include_cses=include_cses,
            composite_leaves=composite_leaves,
        )
