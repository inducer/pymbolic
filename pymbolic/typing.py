"""
Typing helpers
--------------

.. currentmodule:: pymbolic

.. autodata:: Bool
.. autodata:: RealNumber

    Mainly distinguished from :data:`Number` by having a total ordering, i.e.
    not including the complex numbers.

.. autodata:: Number
.. autodata:: Scalar
.. autodata:: ArithmeticExpression

    A narrower type alias than :class:`~pymbolic.typing.Expression` that is returned
    by arithmetic operators, to allow continue doing arithmetic with the result.

.. currentmodule:: pymbolic.typing

.. autodata:: Expression

.. note::

    For backward compatibility, ``pymbolic.Expression``  will alias
    :class:`pymbolic.primitives.ExpressionNode` for now. Once its deprecation
    period is up, it will be removed, and then, in the further future,
    ``pymbolic.Expression`` may become this type alias.

.. autoclass:: ArithmeticOrExpressionT
"""

from __future__ import annotations


__copyright__ = "Copyright (C) 2024 University of Illinois Board of Trustees"

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

from functools import partial
from typing import TYPE_CHECKING, TypeAlias, TypeVar, Union

from pytools import module_getattr_for_deprecations


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
    from pymbolic import ExpressionNode

# Experience with depending packages showed that including Decimal and Fraction
# from the stdlib was more trouble than it's worth because those types don't cleanly
# interoperate with each other.
# (e.g. 'Unsupported operand types for * ("Decimal" and "Fraction")')
# And leaving them out doesn't really make any of this more precise.

_StdlibInexactNumberT = float | complex


if TYPE_CHECKING:
    # Yes, type-checking pymbolic will require numpy. That's OK.
    import numpy as np
    Bool: TypeAlias = bool | np.bool_
    Integer: TypeAlias = int | np.integer
    RealNumber: TypeAlias = Integer | float | np.floating
    InexactNumber: TypeAlias = _StdlibInexactNumberT | np.inexact
else:
    try:
        import numpy as np
    except ImportError:
        Bool = bool
        Integer: TypeAlias = int
        RealNumber: TypeAlias = Integer | float
        InexactNumber: TypeAlias = _StdlibInexactNumberT
    else:
        Bool = bool | np.bool_
        Integer: TypeAlias = int | np.integer
        RealNumber: TypeAlias = Integer | float | np.floating
        InexactNumber: TypeAlias = _StdlibInexactNumberT | np.inexact


Number: TypeAlias = Integer | InexactNumber
Scalar: TypeAlias = Number | Bool

ArithmeticExpression: TypeAlias = Union[Number, "ExpressionNode"]
Expression: TypeAlias = Union[
    Scalar,
    "ExpressionNode",
    tuple["Expression", ...]]
"""A union of types that are considered as part of an expression tree."""

ArithmeticOrExpressionT = TypeVar(
                "ArithmeticOrExpressionT",
                ArithmeticExpression,
                Expression)
"""A type variable that can be either an :class:`~pymbolic.ArithmeticExpression`
or an :class:`~pymbolic.typing.Expression`.
"""

T = TypeVar("T")


__getattr__ = partial(module_getattr_for_deprecations, __name__, {
        "ArithmeticExpressionT": ("ArithmeticExpression", ArithmeticExpression, 2026),
        "ExpressionT": ("Expression", Expression, 2026),
        "IntegerT": ("Integer", Integer, 2026),
        "ScalarT": ("Scalar", Scalar, 2026),
        "BoolT": ("Bool", Bool, 2026),
        })


def not_none(x: T | None) -> T:
    assert x is not None
    return x
