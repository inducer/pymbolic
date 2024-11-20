from __future__ import annotations


"""
Interoperability with :mod:`matchpy.functions` for pattern-matching and
term-rewriting.

.. autofunction:: match
.. autofunction:: match_anywhere
.. autofunction:: replace_all
.. autofunction:: make_replacement_rule


Internal API
^^^^^^^^^^^^

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
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass, field, fields
from functools import partial
from typing import ClassVar, Generic, TypeAlias, TypeVar

from matchpy import (
    Arity,
    Atom as BaseAtom,
    Expression,
    Operation,
    ReplacementRule,
    Wildcard as BaseWildcard,
)

import pymbolic.primitives as p
from pymbolic.typing import Scalar as PbScalar


ExprT: TypeAlias = Expression
ConstantT = TypeVar("ConstantT")
ToMatchpyT = Callable[[p.ExpressionNode], ExprT]
FromMatchpyT = Callable[[ExprT], p.ExpressionNode]


_NOT_OPERAND_METADATA = {"not_an_operand": True}

op_dataclass = dataclass(frozen=True, eq=True, repr=True)
non_operand_field = partial(field, metadata=_NOT_OPERAND_METADATA)


# {{{ Matchable expression types

@op_dataclass
class _Constant(BaseAtom, Generic[ConstantT]):
    value: ConstantT
    variable_name: str | None = None

    @property
    def head(self):
        return self

    def __lt__(self, other):
        # Used by matchpy internally to order subexpressions
        if not isinstance(other, Expression):
            return NotImplemented
        if type(other) is type(self):
            if self.value == other.value:
                return (self.variable_name or "") < (other.variable_name or "")
            return str(self.value) < str(other.value)
        return type(self).__name__ < type(other).__name__


@op_dataclass
class Scalar(_Constant[PbScalar]):
    _mapper_method: str = "map_scalar"


@op_dataclass
class Id(_Constant[str]):
    pass


@op_dataclass
class ComparisonOp(_Constant[str]):
    pass


@op_dataclass
class TupleOp(Operation):
    _operands: tuple[ExprT, ...]
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.variadic
    name: ClassVar[str] = "tuple"
    _mapper_method: ClassVar[str] = "map_tuple_op"
    unpacked_args_to_init: ClassVar[bool] = True

    @property
    def operands(self):
        return self._operands


@op_dataclass
class PymbolicOp(abc.ABC, Operation):
    """
    A base class for all pymbolic-like operations.
    """
    unpacked_args_to_init: ClassVar[bool] = True

    @abc.abstractproperty
    def variable_name(self):
        pass

    @property
    def operands(self) -> tuple[Expression, ...]:
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


@op_dataclass
class Variable(PymbolicOp):
    id: Id
    arity: ClassVar[Arity] = Arity.unary
    variable_name: str | None = non_operand_field(default=None)
    _mapper_method: ClassVar[str] = "map_variable"


@op_dataclass
class Call(PymbolicOp):
    function: ExprT
    args: TupleOp
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.binary
    _mapper_method: ClassVar[str] = "map_call"


@op_dataclass
class Subscript(PymbolicOp):
    aggregate: ExprT
    indices: TupleOp
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.binary
    _mapper_method: ClassVar[str] = "map_subscript"


# {{{ binary ops

@op_dataclass
class _BinaryOp(PymbolicOp):
    x1: ExprT
    x2: ExprT

    arity: ClassVar[Arity] = Arity.binary
    variable_name: str | None = non_operand_field(default=None)


@op_dataclass
class TrueDiv(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_true_div"


@op_dataclass
class FloorDiv(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_floor_div"


@op_dataclass
class Modulo(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_modulo"


@op_dataclass
class Power(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_power"


@op_dataclass
class LeftShift(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_left_shift"


@op_dataclass
class RightShift(_BinaryOp):
    _mapper_method: ClassVar[str] = "map_right_shift"

# }}}


# {{{ variadic ops

variadic_op_dataclass = dataclass(init=False, frozen=True, repr=True)


@variadic_op_dataclass
class _VariadicCommAssocOp(PymbolicOp):
    children: tuple[ExprT, ...]
    variable_name: str | None = non_operand_field(default=None)

    commutative: ClassVar[bool] = True
    associative: ClassVar[bool] = True
    arity: ClassVar[Arity] = Arity.variadic

    def __init__(self, *children: ExprT, variable_name=None):
        object.__setattr__(self, "children", children)
        object.__setattr__(self, "variable_name", variable_name)

    @property
    def operands(self) -> tuple[ExprT, ...]:
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

@op_dataclass
class _UnaryOp(PymbolicOp):
    x: ExprT
    arity: ClassVar[Arity] = Arity.unary
    variable_name: str | None = non_operand_field(default=None)


@op_dataclass
class LogicalNot(_UnaryOp):
    _mapper_method: ClassVar[str] = "map_logical_not"


@op_dataclass
class BitwiseNot(_UnaryOp):
    _mapper_method: ClassVar[str] = "map_bitwise_not"

# }}}


@op_dataclass
class Comparison(PymbolicOp):
    left: ExprT
    operator: ComparisonOp
    right: ExprT
    variable_name: str | None = non_operand_field(default=None)

    arity: ClassVar[Arity] = Arity.ternary
    _mapper_method: ClassVar[str] = "map_comparison"


@op_dataclass
class If(PymbolicOp):
    condition: ExprT
    then: ExprT
    else_: ExprT
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


def match(subject: p.ExpressionNode,
          pattern: p.ExpressionNode,
          to_matchpy_expr: ToMatchpyT | None = None,
          from_matchpy_expr: FromMatchpyT | None = None
          ) -> Iterator[Mapping[str, p.ExpressionNode | PbScalar]]:
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


def match_anywhere(subject: p.ExpressionNode,
                   pattern: p.ExpressionNode,
                   to_matchpy_expr: ToMatchpyT | None = None,
                   from_matchpy_expr: FromMatchpyT | None = None
                   ) -> Iterator[tuple[Mapping[str, p.ExpressionNode | PbScalar],
                                       p.ExpressionNode | PbScalar]
                                 ]:
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


def make_replacement_rule(pattern: p.ExpressionNode,
                          replacement: Callable[..., p.ExpressionNode],
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


def replace_all(expression: p.ExpressionNode,
                rules: Iterable[ReplacementRule],
                to_matchpy_expr: ToMatchpyT | None = None,
                from_matchpy_expr: FromMatchpyT | None = None
                ) -> p.ExpressionNode | tuple[p.ExpressionNode, ...]:
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
