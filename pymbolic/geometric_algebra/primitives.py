from __future__ import division
from __future__ import absolute_import

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

from pymbolic.primitives import Expression, Variable


class MultiVectorVariable(Variable):
    mapper_method = "map_multivector_variable"


# {{{ geometric calculus

class _GeometricCalculusExpression(Expression):
    def stringifier(self):
        from pymbolic.geometric_algebra.mapper import StringifyMapper
        return StringifyMapper


class NablaComponent(_GeometricCalculusExpression):
    def __init__(self, ambient_axis, nabla_id):
        self.ambient_axis = ambient_axis
        self.nabla_id = nabla_id

    def __getinitargs__(self):
        return (self.ambient_axis, self.nabla_id)

    mapper_method = "map_nabla_component"


class Nabla(_GeometricCalculusExpression):
    def __init__(self, nabla_id):
        self.nabla_id = nabla_id

    def __getinitargs__(self):
        return (self.nabla_id,)

    def __getitem__(self, index):
        if not isinstance(index, int):
            raise TypeError("Nabla subscript must be an integer")

        return NablaComponent(index, self.nabla_id)

    mapper_method = "map_nabla"


class DerivativeSource(_GeometricCalculusExpression):
    def __init__(self, operand, nabla_id=None):
        self.operand = operand
        self.nabla_id = nabla_id

    def __getinitargs__(self):
        return (self.operand, self.nabla_id)

    mapper_method = "map_derivative_source"


class Derivative(object):
    _next_id = [0]

    def __init__(self):
        self.my_id = "id%s" % self._next_id[0]
        self._next_id[0] += 1

    @property
    def nabla(self):
        return Nabla(self.my_id)

    def __call__(self, operand):
        from pymbolic.geometric_algebra import MultiVector
        if isinstance(operand, MultiVector):
            return operand.map(
                    lambda coeff: DerivativeSource(coeff, self.my_id))
        else:
            return DerivativeSource(operand, self.my_id)

# }}}

# vim: foldmethod=marker
