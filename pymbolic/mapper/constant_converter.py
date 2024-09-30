from __future__ import annotations


__copyright__ = "Copyright (C) 2017 Andreas Kloeckner"

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

import pymbolic.mapper


class ConstantToNumpyConversionMapper(pymbolic.mapper.IdentityMapper):
    """Because of `this numpy bug <https://github.com/numpy/numpy/issues/9438>`__,
    sized :mod:`numpy` number (i.e. ones with definite bit width, such as
    :class:`numpy.complex64`) have a low likelihood of surviving expression
    construction.

    This mapper ensures that all occurring numerical constants are of the
    expected type.
    """

    def __init__(self, real_type, complex_type=None, integer_type=None):
        import numpy as np
        self.real_type = real_type

        if complex_type is None:
            if real_type is np.float32:
                complex_type = np.complex64
            elif real_type is np.float64:
                complex_type = np.complex128
            elif real_type is np.float128:  # pylint:disable=no-member
                complex_type = np.complex256  # pylint:disable=no-member
            else:
                raise TypeError("unable to determine corresponding complex type "
                        f"for '{real_type.__name__}'")

        self.complex_type = complex_type

        self.integer_type = integer_type

    def map_constant(self, expr):
        if expr.imag:
            return self.complex_type(expr)

        expr = expr.real

        if int(expr) == expr and not isinstance(expr, float):
            if self.integer_type is not None:
                return self.integer_type(expr)
            else:
                return expr
        else:
            return self.real_type(expr)
