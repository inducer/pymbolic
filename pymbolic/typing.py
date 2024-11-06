"""
.. currentmodule:: pymbolic

Typing helpers
--------------

.. autoclass:: BoolT
.. autoclass:: NumberT
.. autoclass:: ScalarT
.. autoclass:: ArithmeticExpressionT

    A narrower type alias than :class:`ExpressionT` that is returned by
    arithmetic operators, to allow continue doing arithmetic with the result
    of arithmetic.

.. autoclass:: ExpressionT

.. currentmodule:: pymbolic.typing

.. autoclass:: ArithmeticOrExpressionT

    A type variable that can be either :data:`ArithmeticExpressionT`
    or :data:`ExpressionT`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, TypeVar, Union


# FIXME: This is a lie. Many more constant types (e.g. numpy and such)
# are in practical use and completely fine. We cannot really add in numpy
# as a special case (because pymbolic doesn't have a hard numpy dependency),
# and there isn't a usable numerical tower that we could rely on. As such,
# code abusing what constants are allowable will have to type-ignore those
# statements. Better ideas would be most welcome.
#
# References:
# https://github.com/python/mypy/issues/3186
# https://discuss.python.org/t/numeric-generics-where-do-we-go-from-pep-3141-and-present-day-mypy/17155/14

# FIXME: Maybe we should define scalar types via a protocol?
# Pymbolic doesn't particularly restrict scalars to these, this
# just reflects common usage. See typeshed for possible inspiration:
# https://github.com/python/typeshed/blob/119cd09655dcb4ed7fb2021654ba809b8d88846f/stdlib/numbers.pyi

if TYPE_CHECKING:
    from pymbolic.primitives import Expression

# Experience with depending packages showed that including Decimal and Fraction
# from the stdlib was more trouble than it's worth because those types don't cleanly
# interoperate with each other.
# (e.g. 'Unsupported operand types for * ("Decimal" and "Fraction")')
# And leaving them out doesn't really make any of this more precise.

_StdlibInexactNumberT = float | complex


if TYPE_CHECKING:
    # Yes, type-checking pymbolic will require numpy. That's OK.
    import numpy as np
    BoolT = bool | np.bool_
    IntegerT: TypeAlias = int | np.integer
    InexactNumberT: TypeAlias = _StdlibInexactNumberT | np.inexact
else:
    try:
        import numpy as np
    except ImportError:
        BoolT = bool
        IntegerT: TypeAlias = int
        InexactNumberT: TypeAlias = _StdlibInexactNumberT
    else:
        BoolT = bool | np.bool_
        IntegerT: TypeAlias = int | np.integer
        InexactNumberT: TypeAlias = _StdlibInexactNumberT | np.inexact


NumberT: TypeAlias = IntegerT | InexactNumberT
ScalarT: TypeAlias = NumberT | BoolT

_ScalarOrExpression = Union[ScalarT, "Expression"]
ArithmeticExpressionT: TypeAlias = Union[NumberT, "Expression"]

ExpressionT: TypeAlias = _ScalarOrExpression | tuple["ExpressionT", ...]

ArithmeticOrExpressionT = TypeVar(
                "ArithmeticOrExpressionT",
                ArithmeticExpressionT,
                ExpressionT)


T = TypeVar("T")


def not_none(x: T | None) -> T:
    assert x is not None
    return x
