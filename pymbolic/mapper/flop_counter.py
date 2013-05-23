from __future__ import division

__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

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

from pymbolic.mapper import CombineMapper




class FlopCounter(CombineMapper):
    def combine(self, values):
        return sum(values)

    def map_constant(self, expr):
        return 0

    def map_variable(self, expr):
        return 0

    def map_sum(self, expr):
        if expr.children:
            return len(expr.children) - 1 + sum(self.rec(ch) for ch in expr.children)
        else:
            return 0

    map_product = map_sum

    def map_quotient(self, expr, *args):
        return 1 + self.rec(expr.numerator) + self.rec(expr.denominator)

    map_floor_div = map_quotient

    def map_power(self, expr, *args):
        return 1 + self.rec(expr.base) + self.rec(expr.exponent)

    def map_if_positive(self, expr):
        return self.rec(expr.criterion) + max(
                self.rec(expr.then),
                self.rec(expr.else_))
