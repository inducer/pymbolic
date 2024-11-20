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

from collections.abc import Hashable
from typing import ClassVar

from pymbolic.primitives import ExpressionNode, Variable, expr_dataclass
from pymbolic.typing import Expression


class MultiVectorVariable(Variable):
    mapper_method = "map_multivector_variable"


# {{{ geometric calculus

class _GeometricCalculusExpression(ExpressionNode):
    def stringifier(self):
        from pymbolic.geometric_algebra.mapper import StringifyMapper
        return StringifyMapper


@expr_dataclass()
class NablaComponent(_GeometricCalculusExpression):
    ambient_axis: int
    nabla_id: Hashable


@expr_dataclass()
class Nabla(_GeometricCalculusExpression):
    nabla_id: Hashable


@expr_dataclass()
class DerivativeSource(_GeometricCalculusExpression):
    operand: Expression
    nabla_id: Hashable


class Derivative:
    """This mechanism cannot be used to take more than one derivative at a time.

    .. autoproperty:: nabla
    .. automethod:: __call__
    .. automethod:: dnabla
    .. automethod:: resolve
    """
    _next_id: ClassVar[list[int]] = [0]

    def __init__(self):
        self.my_id = f"id{self._next_id[0]}"
        self._next_id[0] += 1

    @property
    def nabla(self):
        return Nabla(self.my_id)

    def dnabla(self, ambient_dim):
        from pytools.obj_array import make_obj_array

        from pymbolic.geometric_algebra import MultiVector
        return MultiVector(make_obj_array(
            [NablaComponent(axis, self.my_id)
                for axis in range(ambient_dim)]))

    def __call__(self, operand):
        from pymbolic.geometric_algebra import MultiVector
        if isinstance(operand, MultiVector):
            return operand.map(
                    lambda coeff: DerivativeSource(coeff, self.my_id))
        else:
            return DerivativeSource(operand, self.my_id)

    @staticmethod
    def resolve(expr):
        # This method will need to be overridden by codes using this
        # infrastructure to use the appropriate subclass of DerivativeBinder.

        from pymbolic.geometric_algebra.mapper import DerivativeBinder
        return DerivativeBinder()(expr)

# }}}

# vim: foldmethod=marker
