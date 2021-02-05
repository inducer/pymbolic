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


class Derivative:
    """This mechanism cannot be used to take more than one derivative at a time.

    .. autoproperty:: nabla
    .. automethod:: __call__
    .. automethod:: dnabla
    .. automethod:: resolve
    """
    _next_id = [0]

    def __init__(self):
        self.my_id = f"id{self._next_id[0]}"
        self._next_id[0] += 1

    @property
    def nabla(self):
        return Nabla(self.my_id)

    def dnabla(self, ambient_dim):
        from pymbolic.geometric_algebra import MultiVector
        from pytools.obj_array import make_obj_array
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
        # This method will need to be overriden by codes using this
        # infrastructure to use the appropriate subclass of DerivativeBinder.

        from pymbolic.geometric_algebra.mapper import DerivativeBinder
        return DerivativeBinder()(expr)

# }}}

# vim: foldmethod=marker
