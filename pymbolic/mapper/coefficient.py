__copyright__ = "Copyright (C) 2013 Andreas Kloeckner"

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

from pymbolic.mapper import Mapper


class CoefficientCollector(Mapper):
    def __init__(self, target_names=None):
        self.target_names = target_names

    def map_sum(self, expr):
        stride_dicts = [self.rec(ch) for ch in expr.children]

        result = {}
        for stride_dict in stride_dicts:
            for var, stride in stride_dict.items():
                if var in result:
                    result[var] += stride
                else:
                    result[var] = stride

        return result

    def map_product(self, expr):
        result = {}

        children_coeffs = [self.rec(child) for child in expr.children]

        idx_of_child_with_vars = None
        for i, child_coeffs in enumerate(children_coeffs):
            for k in child_coeffs:
                if k != 1:
                    if (idx_of_child_with_vars is not None
                            and idx_of_child_with_vars != i):
                        raise RuntimeError(
                                "nonlinear expression")
                    idx_of_child_with_vars = i

        other_coeffs = 1
        for i, child_coeffs in enumerate(children_coeffs):
            if i != idx_of_child_with_vars:
                assert len(child_coeffs) == 1
                other_coeffs *= child_coeffs[1]

        if idx_of_child_with_vars is None:
            return {1: other_coeffs}
        else:
            return {
                    var: other_coeffs*coeff
                    for var, coeff in
                    children_coeffs[idx_of_child_with_vars].items()}

        return result

    def map_quotient(self, expr):
        from pymbolic.primitives import Quotient
        d_num = self.rec(expr.numerator)
        d_den = self.rec(expr.denominator)
        # d_den should look like {1: k}
        if len(d_den) > 1 or 1 not in d_den:
            raise RuntimeError("nonlinear expression")
        val = d_den[1]
        for k in d_num.keys():
            d_num[k] *= Quotient(1, val)
        return d_num

    def map_power(self, expr):
        d_base = self.rec(expr.base)
        d_exponent = self.rec(expr.exponent)
        # d_exponent should look like {1: k}
        if len(d_exponent) > 1 or 1 not in d_exponent:
            raise RuntimeError("nonlinear expression")
        # d_base should look like {1: k}
        if len(d_base) > 1 or 1 not in d_base:
            raise RuntimeError("nonlinear expression")
        return {1: expr}

    def map_constant(self, expr):
        return {1: expr}

    def map_algebraic_leaf(self, expr):
        if self.target_names is None or expr.name in self.target_names:
            return {expr: 1}
        else:
            return {1: expr}
