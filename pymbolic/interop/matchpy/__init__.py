from __future__ import annotations


__doc__ = """
Interoperability with :mod:`matchpy.functions` for pattern-matching and
term-rewriting.

.. autofunction:: match
.. autofunction:: match_anywhere
.. autofunction:: replace_all
.. autofunction:: make_replacement_rule

Internal API
^^^^^^^^^^^^

.. autoclass:: ToMatchpyT
.. autoclass:: FromMatchpyT

.. autoclass:: PymbolicOp
.. autoclass:: Wildcard
"""

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

import abc
from dataclasses import dataclass, field, fields
from functools import partial
from typing import TYPE_CHECKING, ClassVar, Generic, TypeAlias, TypeVar

from matchpy import (
    Arity,
    Atom,
    Expression as MatchpyExpression,
    Operation,
    ReplacementRule,
    Wildcard as BaseWildcard,
)
from typing_extensions import dataclass_transform

from pymbolic.typing import Expression as _Expression, Scalar as _Scalar


if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping

    from pymbolic.primitives import ExpressionNode


ConstantT = TypeVar("ConstantT")
ToMatchpyT: TypeAlias = "Callable[[_Expression], MatchpyExpression]"
FromMatchpyT: TypeAlias = "Callable[[MatchpyExpression], _Expression]"


_NOT_OPERAND_METADATA = {"not_an_operand": True}

_T = TypeVar("_T")


non_operand_field = partial(field, metadata=_NOT_OPERAND_METADATA)


@dataclass_transform(frozen_default=True, field_specifiers=(field,))
def op_dataclass(
        ) -> Callable[[type[_T]], type[_T]]:

    def map_cls(cls: type[_T]) -> type[_T]:
        return dataclass(init=True, eq=True, repr=True, frozen=True)(cls)

    return map_cls


# {{{ Matchable expression types

@op_dataclass()
class _Constant(Atom, Generic[ConstantT]):
    value: ConstantT
    variable_name: str | None = None

    @property
    def head(self):
        return self

    def __lt__(self, other: object) -> bool:
        # Used by matchpy internally to order subexpressions
        if not isinstance(other, MatchpyExpression):
            return NotImplemented
        if type(other) is type(self):
            if self.value == other.value:
                return (self.variable_name or "") < (other.variable_name or "")
            return str(self.value) < str(other.value)
        return type(self).__name__ < type(other).__name__


@op_dataclass()
class Scalar(_Constant[_Scalar]):
    _mapper_method: str = "map_scalar"


@op_dataclass()
class Id(_Constant[str]):
    pass


@op_dataclass()
class ComparisonOp(_Constant[str]):
    pass


@op_dataclass()
class TupleOp(Operation):
    _operands: tuple[MatchpyExpression, ...]
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.variadic
    name: ClassVar[str] = "tuple"
    _mapper_method: ClassVar[str] = "map_tuple_op"
    unpacked_args_to_init: ClassVar[bool] = True

    @property
    def operands(self):
        return self._operands


@op_dataclass()
class PymbolicOp(abc.ABC, Operation):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """
    A base class for all pymbolic-like operations.
    """
    unpacked_args_to_init: ClassVar[bool] = True

    @abc.abstractproperty
    def variable_name(self):
        pass

    @property
    def operands(self) -> tuple[MatchpyExpression, ...]:
        return tuple(getattr(self, field.name)
                     for field in fields(self)
                     if not field.metadata.get("not_an_operand", False))

    def __lt__(self, other):
        if type(other) is type(self):
            if self.operands == other.operands:
                return (self.variable_name or "") < (other.variable_name or "")
            return str(self.operands) < str(other.operands)
        return type(self).__name__ < type(other).__name__

    @property
    def name(self) -> str:
        return self.__class__.__name__


@op_dataclass()
class Variable(PymbolicOp):
    id: Id
    arity: ClassVar[Arity] = Arity.unary
    variable_name: str | None = non_operand_field(default=None)
    _mapper_method: ClassVar[str] = "map_variable"


@op_dataclass()
class Call(PymbolicOp):
    function: MatchpyExpression
    args: TupleOp
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.binary
    _mapper_method: ClassVar[str] = "map_call"


@op_dataclass()
class Subscript(PymbolicOp):
    aggregate: MatchpyExpression
    indices: TupleOp
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.binary
    _mapper_method: ClassVar[str] = "map_subscript"


# {{{ binary ops

@op_dataclass()
class _BinaryOp(PymbolicOp):
    x1: MatchpyExpression
    x2: MatchpyExpression

    arity: ClassVar[Arity] = Arity.binary
    variable_name: str | None = non_operand_field(default=None)


@op_dataclass()
class TrueDiv(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_true_div"


@op_dataclass()
class FloorDiv(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_floor_div"


@op_dataclass()
class Modulo(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_modulo"


@op_dataclass()
class Power(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_power"


@op_dataclass()
class LeftShift(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_left_shift"


@op_dataclass()
class RightShift(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_right_shift"

# }}}


# {{{ variadic ops

variadic_op_dataclass = dataclass(init=False, frozen=True, repr=True)


@variadic_op_dataclass
class _VariadicCommAssocOp(PymbolicOp):
    children: tuple[MatchpyExpression, ...]
    variable_name: str | None = non_operand_field(default=None)

    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True
    arity: ClassVar[Arity] = Arity.variadic

    def __init__(self, *children: MatchpyExpression, variable_name=None):
        object.__setattr__(self, "children", children)
        object.__setattr__(self, "variable_name", variable_name)

    @property
    def operands(self) -> tuple[MatchpyExpression, ...]:
        return self.children


@variadic_op_dataclass
class Sum(_VariadicCommAssocOp):
    _mapper_method: ClassVar[str] = "map_sum"


@variadic_op_dataclass
class Product(_VariadicCommAssocOp):
    _mapper_method: ClassVar[str] = "map_product"


@variadic_op_dataclass
class LogicalOr(_VariadicCommAssocOp):
    _mapper_method: ClassVar[str] = "map_logical_or"


@variadic_op_dataclass
class LogicalAnd(_VariadicCommAssocOp):
    _mapper_method: ClassVar[str] = "map_logical_and"


@variadic_op_dataclass
class BitwiseOr(_VariadicCommAssocOp):
    _mapper_method: ClassVar[str] = "map_bitwise_or"


@variadic_op_dataclass
class BitwiseAnd(_VariadicCommAssocOp):
    _mapper_method: ClassVar[str] = "map_bitwise_and"


@variadic_op_dataclass
class BitwiseXor(_VariadicCommAssocOp):
    _mapper_method: ClassVar[str] = "map_bitwise_xor"

# }}}


# {{{ unary op

@op_dataclass()
class _UnaryOp(PymbolicOp):
    x: MatchpyExpression
    arity: ClassVar[Arity] = Arity.unary
    variable_name: str | None = non_operand_field(default=None)


@op_dataclass()
class LogicalNot(_UnaryOp):
    _mapper_method: ClassVar[str] = "map_logical_not"


@op_dataclass()
class BitwiseNot(_UnaryOp):
    _mapper_method: ClassVar[str] = "map_bitwise_not"

# }}}


@op_dataclass()
class Comparison(PymbolicOp):
    left: MatchpyExpression
    operator: ComparisonOp
    right: MatchpyExpression
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.ternary
    _mapper_method: ClassVar[str] = "map_comparison"


@op_dataclass()
class If(PymbolicOp):
    condition: MatchpyExpression
    then: MatchpyExpression
    else_: MatchpyExpression
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.ternary
    _mapper_method: ClassVar[str] = "map_if"


class Wildcard(BaseWildcard):

    # {{{ FIXME: This should go into matchpy itself.

    @classmethod
    def dot(cls, name=None) -> Wildcard:
        return cls(min_count=1, fixed_size=True, variable_name=name)

    @classmethod
    def star(cls, name=None) -> Wildcard:
        # FIXME: This should go into matchpy itself.
        return cls(min_count=0, fixed_size=False, variable_name=name)

    @classmethod
    def plus(cls, name=None) -> Wildcard:
        # FIXME: This should go into matchpy itself.
        return cls(min_count=1, fixed_size=False, variable_name=name)

    # }}}

# }}}


def _get_operand_at_path(expr: PymbolicOp, path: tuple[int, ...]) -> PymbolicOp:
    result = expr

    while path:
        step, path = path[0], path[1:]
        result = result.operands[step]

    return result


def match(subject: ExpressionNode,
          pattern: ExpressionNode,
          to_matchpy_expr: ToMatchpyT | None = None,
          from_matchpy_expr: FromMatchpyT | None = None
          ) -> Iterator[Mapping[str, _Expression]]:
    from matchpy import Pattern, match

    from .tofrom import FromMatchpyExpressionMapper, ToMatchpyExpressionMapper

    if to_matchpy_expr is None:
        to_matchpy_expr = ToMatchpyExpressionMapper()
    if from_matchpy_expr is None:
        from_matchpy_expr = FromMatchpyExpressionMapper()

    m_subject = to_matchpy_expr(subject)
    m_pattern = Pattern(to_matchpy_expr(pattern))
    matches = match(m_subject, m_pattern)

    for subst in matches:
        yield {name: from_matchpy_expr(expr)
               for name, expr in subst.items()}


def match_anywhere(subject: ExpressionNode,
                   pattern: ExpressionNode,
                   to_matchpy_expr: ToMatchpyT | None = None,
                   from_matchpy_expr: FromMatchpyT | None = None
                   ) -> Iterator[tuple[Mapping[str, _Expression], _Expression]]:
    from matchpy import Pattern, match_anywhere

    from .tofrom import FromMatchpyExpressionMapper, ToMatchpyExpressionMapper

    if to_matchpy_expr is None:
        to_matchpy_expr = ToMatchpyExpressionMapper()
    if from_matchpy_expr is None:
        from_matchpy_expr = FromMatchpyExpressionMapper()

    m_subject = to_matchpy_expr(subject)
    m_pattern = Pattern(to_matchpy_expr(pattern))
    matches = match_anywhere(m_subject, m_pattern)

    for subst, path in matches:
        yield ({name: from_matchpy_expr(expr)
                for name, expr in subst.items()},
               from_matchpy_expr(_get_operand_at_path(m_subject, path)))


def make_replacement_rule(pattern: _Expression,
                          replacement: Callable[..., _Expression],
                          to_matchpy_expr: ToMatchpyT | None = None,
                          from_matchpy_expr: FromMatchpyT | None = None
                          ) -> ReplacementRule:
    """
    Returns a :class:`matchpy.functions.ReplacementRule` from the objects
    declared via :mod:`pymbolic.primitives` instances.
    """
    from matchpy import Pattern

    from .tofrom import (
        FromMatchpyExpressionMapper,
        ToFromReplacement,
        ToMatchpyExpressionMapper,
    )

    if to_matchpy_expr is None:
        to_matchpy_expr = ToMatchpyExpressionMapper()
    if from_matchpy_expr is None:
        from_matchpy_expr = FromMatchpyExpressionMapper()

    m_pattern = Pattern(to_matchpy_expr(pattern))
    return ReplacementRule(m_pattern, ToFromReplacement(replacement,
                                                        to_matchpy_expr,
                                                        from_matchpy_expr))


def replace_all(expression: _Expression,
                rules: Iterable[ReplacementRule],
                to_matchpy_expr: ToMatchpyT | None = None,
                from_matchpy_expr: FromMatchpyT | None = None
                ) -> _Expression:
    import collections.abc as abc

    from matchpy import replace_all

    from .tofrom import FromMatchpyExpressionMapper, ToMatchpyExpressionMapper

    if to_matchpy_expr is None:
        to_matchpy_expr = ToMatchpyExpressionMapper()
    if from_matchpy_expr is None:
        from_matchpy_expr = FromMatchpyExpressionMapper()

    m_expr = to_matchpy_expr(expression)
    result = replace_all(m_expr, rules)
    if isinstance(result, abc.Sequence):
        return tuple(from_matchpy_expr(e) for e in result)
    else:
        return from_matchpy_expr(result)

# vim: fdm=marker
