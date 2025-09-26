"""
.. autoclass:: SubstitutionMapper
.. autoclass:: CachedSubstitutionMapper
.. autofunction:: make_subst_func
.. autofunction:: substitute
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

from typing import TYPE_CHECKING, Any, Protocol, TypeVar

from typing_extensions import override

from pymbolic.mapper import CachedIdentityMapper, IdentityMapper


if TYPE_CHECKING:
    from collections.abc import Callable, Set

    import optype

    from pymbolic.primitives import AlgebraicLeaf, Lookup, Subscript, Variable
    from pymbolic.typing import Expression

    _KT_co = TypeVar("_KT_co", covariant=True)
    _VT_co = TypeVar("_VT_co", covariant=True)

    class CanItems(Protocol[_KT_co, _VT_co]):
        def items(self) -> Set[tuple[_KT_co, _VT_co]]: ...


class SubstitutionMapper(IdentityMapper[[]]):
    subst_func: Callable[[AlgebraicLeaf], Expression | None]

    def __init__(
            self, subst_func: Callable[[AlgebraicLeaf], Expression | None]
        ) -> None:
        super().__init__()
        self.subst_func = subst_func

    @override
    def map_variable(self, expr: Variable) -> Expression:
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return expr

    @override
    def map_subscript(self, expr: Subscript) -> Expression:
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return IdentityMapper.map_subscript(self, expr)

    @override
    def map_lookup(self, expr: Lookup) -> Expression:
        result = self.subst_func(expr)
        if result is not None:
            return result
        else:
            return IdentityMapper.map_lookup(self, expr)


class CachedSubstitutionMapper(CachedIdentityMapper[[]], SubstitutionMapper):
    def __init__(
        self, subst_func: Callable[[AlgebraicLeaf], Expression | None]
    ) -> None:
        SubstitutionMapper.__init__(self, subst_func)
        super().__init__(subst_func)


def make_subst_func(
    # "Any" here avoids the whole Mapping variance disaster
    # e.g. https://github.com/python/typing/issues/445
    variable_assignments: optype.CanGetitem[Any, Expression],
) -> Callable[[AlgebraicLeaf], Expression | None]:
    import pymbolic.primitives as primitives

    def subst_func(var: AlgebraicLeaf) -> Expression | None:
        try:
            return variable_assignments[var]
        except KeyError:
            if isinstance(var, primitives.Variable):
                try:
                    return variable_assignments[var.name]
                except KeyError:
                    return None
            else:
                return None

    return subst_func


def substitute(
    expression: Expression,
    variable_assignments: CanItems[AlgebraicLeaf | str, Expression] | None
    = None,
    mapper_cls=CachedSubstitutionMapper,
    **kwargs: Expression,
):
    """
    :arg mapper_cls: A :class:`type` of the substitution mapper
        whose instance applies the substitution.
    """
    if variable_assignments is None:
        # "Any" here avoids pointless grief about variance
        # e.g. https://github.com/python/typing/issues/445
        v_ass_copied: dict[Any, Expression] = {}
    else:
        v_ass_copied = dict(variable_assignments.items())

    v_ass_copied.update(kwargs)

    return mapper_cls(make_subst_func(v_ass_copied))(expression)
