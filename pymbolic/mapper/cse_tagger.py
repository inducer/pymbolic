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


from pymbolic.mapper import WalkMapper, IdentityMapper
from pymbolic.primitives import CommonSubexpression


class CSEWalkMapper(WalkMapper):
    def __init__(self):
        self.subexpr_histogram = {}

    def visit(self, expr):
        self.subexpr_histogram[expr] = self.subexpr_histogram.get(expr, 0) + 1
        return True


class CSETagMapper(IdentityMapper):
    def __init__(self, walk_mapper):
        self.subexpr_histogram = walk_mapper.subexpr_histogram

    def map_call(self, expr):
        if self.subexpr_histogram.get(expr, 0) > 1:
            return CommonSubexpression(expr)
        else:
            return getattr(IdentityMapper, expr.mapper_method)(
                    self, expr)

    map_sum = map_call
    map_product = map_call
    map_quotient = map_call
    map_floor_div = map_call
    map_remainder = map_call
    map_power = map_call
    map_polynomial = map_call

    map_left_shift = map_call
    map_right_shift = map_call

    map_bitwise_not = map_call
    map_bitwise_or = map_call
    map_bitwise_xor = map_call
    map_bitwise_and = map_call

    map_comparison = map_call

    map_logical_not = map_call
    map_logical_and = map_call
    map_logical_or = map_call

    map_if = map_call
    map_if_positive = map_call
