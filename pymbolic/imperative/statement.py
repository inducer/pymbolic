"""Instruction types"""
from __future__ import annotations


__copyright__ = "Copyright (C) 2015 Matt Wala, Andreas Kloeckner"

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

from dataclasses import dataclass, replace
from sys import intern
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeVar, cast

from typing_extensions import Self, override

from pymbolic.typing import Expression, not_none


if TYPE_CHECKING:
    from collections.abc import Callable, Set

    from pymbolic.primitives import Variable


# {{{ statement classes

class BasicStatementLike(Protocol):
    @property
    def id(self) -> str: ...
    @property
    def depends_on(self) -> Set[str]: ...

    def copy(self, **kwargs: object) -> Self: ...


BasicStatementLikeT = TypeVar("BasicStatementLikeT", bound=BasicStatementLike)


class StatementLike(BasicStatementLike, Protocol):
    def get_written_variables(self) -> Set[str]: ...

    def get_read_variables(self) -> Set[str]: ...

    def map_expressions(self,
                mapper: Callable[[Expression], Expression],
                include_lhs: bool = True
            ) -> Self: ...


StatementLikeT = TypeVar("StatementLikeT", bound=StatementLike)


@dataclass(frozen=True)
class Statement:
    """
    .. autoattribute:: depends_on
    .. autoattribute:: id

    .. automethod:: get_written_variables
    .. automethod:: get_read_variables
    """
    id: str
    """
    A string, a unique identifier for this instruction.
    """

    depends_on: Set[str]
    """A :class:`frozenset` of instruction ids that are reuqired to be
    executed within this execution context before this instruction can be
    executed."""

    def __post_init__(self):
        if isinstance(self.id, str):
            object.__setattr__(self, "id", intern(self.id))

    def get_written_variables(self) -> Set[str]:
        """Returns a :class:`frozenset` of variables being written by this
        instruction.
        """
        return frozenset()

    def get_read_variables(self) -> Set[str]:
        """Returns a :class:`frozenset` of variables being read by this
        instruction.
        """
        return frozenset()

    def map_expressions(self,
                mapper: Callable[[Expression], Expression],
                include_lhs: bool = True
            ) -> Self:
        """Returns a new copy of *self* with all expressions
        replaced by ``mapepr(expr)`` for every
        :class:`pymbolic.primitives.Expression`
        contained in *self*.
        """
        return self

    def get_dependency_mapper(self,
                include_calls: bool | Literal["descend_args"] = True,
            ):
        from pymbolic.mapper.dependency import DependencyMapper
        return DependencyMapper[[]](
            include_subscripts=False,
            include_lookups=False,
            include_calls=include_calls)

    def copy(self, **kwargs: Any) -> Self:  # pyright: ignore[reportAny]
        return replace(self, **kwargs)

# }}}


# {{{ statement with condition

@dataclass(frozen=True)
class ConditionalStatement(Statement):
    __doc__ = not_none(Statement.__doc__) + """
    .. autoattribute:: condition
    """

    condition: Expression
    """The instruction condition as a :mod:`pymbolic` expression (`True` if the
    instruction is unconditionally executed)"""

    def _condition_printing_suffix(self):
        if self.condition is True:
            return ""
        return " if " + str(self.condition)

    @override
    def __str__(self):
        return (super().__str__()
                + self._condition_printing_suffix())

    @override
    def get_read_variables(self) -> Set[str]:
        dep_mapper = self.get_dependency_mapper()
        return (
                super().get_read_variables()
                | frozenset(
                    cast("Variable", dep).name for dep in dep_mapper(self.condition)))

# }}}


# {{{ assignment

@dataclass(frozen=True)
class Assignment(Statement):
    """
    .. attribute:: lhs
    .. attribute:: rhs
    """

    lhs: Expression
    rhs: Expression

    @override
    def get_written_variables(self):
        from pymbolic.primitives import Subscript, Variable
        if isinstance(self.lhs, Variable):
            return frozenset([self.lhs.name])
        elif isinstance(self.lhs, Subscript):
            assert isinstance(self.lhs.aggregate, Variable)
            return frozenset([self.lhs.aggregate.name])
        else:
            raise TypeError("unexpected type of LHS")

    @override
    def get_read_variables(self) -> Set[str]:
        result = super().get_read_variables()
        get_deps = self.get_dependency_mapper()

        def get_vars(expr: Expression):
            return frozenset(cast("Variable", dep).name for dep in get_deps(expr))

        result = get_vars(self.rhs) | get_vars(self.lhs)

        return result

    @override
    def map_expressions(self,
                mapper: Callable[[Expression], Expression],
                include_lhs: bool = True
            ) -> Self:
        return (super()
                .map_expressions(mapper, include_lhs=include_lhs)
                .copy(
                    lhs=mapper(self.lhs) if include_lhs else self.lhs,
                    rhs=mapper(self.rhs)))

    @override
    def __str__(self):
        result = "{assignee} <- {expr}".format(
            assignee=str(self.lhs),
            expr=str(self.rhs),)

        return result

# }}}


# {{{ conditional assignment

@dataclass(frozen=True)
class ConditionalAssignment(ConditionalStatement, Assignment):
    @override
    def map_expressions(self,
                mapper: Callable[[Expression], Expression],
                include_lhs: bool = True
            ) -> Self:
        return (super()
                .map_expressions(mapper, include_lhs=include_lhs)
                .copy(condition=mapper(self.condition)))

# }}}


# {{{ nop

@dataclass(frozen=True)
class Nop(Statement):
    def __str__(self):
        return "nop"

# }}}


Instruction = Statement
ConditionalInstruction = ConditionalStatement


# vim: foldmethod=marker
