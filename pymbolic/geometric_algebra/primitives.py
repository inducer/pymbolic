from __future__ import annotations


__copyright__ = "Copyright (C) 2014 Andreas Kloeckner"

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

# This is experimental, undocumented, and could go away any second.
# Consider yourself warned.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, TypeAlias, TypeVar

import pytools.obj_array as obj_array

from pymbolic.geometric_algebra import MultiVector
from pymbolic.primitives import ExpressionNode, Variable, expr_dataclass


if TYPE_CHECKING:
    from collections.abc import Hashable

    from pymbolic.typing import ArithmeticExpression, Expression


class MultiVectorVariable(Variable):
    mapper_method: ClassVar[str] = "map_multivector_variable"


# {{{ geometric calculus

class _GeometricCalculusExpression(ExpressionNode):
    def stringifier(self, originating_stringifier=None):
        from pymbolic.geometric_algebra.mapper import StringifyMapper
        return StringifyMapper()


NablaId: TypeAlias = "Hashable"

# TODO: move these somewhere pytential can make use of them.
# Maybe just `pymbolic.typing`? (this module is not yet stable and documented)

Operand: TypeAlias = """
    ArithmeticExpression
    | MultiVector[ArithmeticExpression]
    | obj_array.ObjectArray1D[ArithmeticExpression]
    | obj_array.ObjectArray2D[ArithmeticExpression]
    | obj_array.ObjectArrayND[ArithmeticExpression]"""
r"""A type alias for allowable expressions that can act as an operand in
arithmetic. This includes expressions, but also
:class:`~pymbolic.geometry_algebra.MultiVector`\ s and (object) :mod:`numpy` arrays.
"""
OperandTc = TypeVar(
    "OperandTc",
    "ArithmeticExpression",
    "MultiVector[ArithmeticExpression]",
    "obj_array.ObjectArray1D[ArithmeticExpression]",
    "obj_array.ObjectArray2D[ArithmeticExpression]",
    "obj_array.ObjectArrayND[ArithmeticExpression]",
)
"""A :class:`~typing.TypeVar` constrained to the types in :class:`Operand`. Note
that this does not use :class:`Operand` as a bound.
"""


@expr_dataclass()
class NablaComponent(_GeometricCalculusExpression):
    """
    .. autoattribute:: ambient_axis
    .. autoattribute:: NablaId
    """
    ambient_axis: int
    nabla_id: NablaId


@expr_dataclass()
class Nabla(_GeometricCalculusExpression):
    """
    .. autoattribute:: nabla_id
    """
    nabla_id: NablaId


@expr_dataclass()
class DerivativeSource(_GeometricCalculusExpression):
    """
    .. autoattribute:: operand
    .. autoattribute:: nabla_id
    """
    operand: Expression
    nabla_id: Hashable


class Derivative(ABC):
    """This mechanism cannot be used to take more than one derivative at a time.

    .. autoproperty:: nabla
    .. automethod:: dnabla
    .. automethod:: resolve
    .. automethod:: __call__
    """

    my_id: str
    _next_id: ClassVar[list[int]] = [0]

    def __init__(self) -> None:
        self.my_id = f"id{self._next_id[0]}"
        self._next_id[0] += 1

    @property
    def nabla(self) -> Nabla:
        return Nabla(self.my_id)

    def dnabla(self, ambient_dim: int) -> MultiVector[ArithmeticExpression]:
        nablas: list[ArithmeticExpression] = [
            NablaComponent(axis, self.my_id)
            for axis in range(ambient_dim)]
        return MultiVector(obj_array.new_1d(nablas))

    def __call__(self, operand: OperandTc) -> OperandTc:
        from pymbolic.geometric_algebra import componentwise

        def func(coeff: ArithmeticExpression) -> ArithmeticExpression:
            return DerivativeSource(coeff, self.my_id)

        return componentwise(func, operand)  # pyright: ignore[reportReturnType]

    @staticmethod
    @abstractmethod
    def resolve(expr: Expression) -> Expression:
        # This method will need to be overridden by codes using this
        # infrastructure to use the appropriate subclass of DerivativeBinder.
        pass

# }}}

# vim: foldmethod=marker
