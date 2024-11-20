"""
.. autoclass:: DistributeMapper
.. autofunction:: distribute
"""
from __future__ import annotations


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

from typing import cast

import pymbolic
import pymbolic.primitives as p
from pymbolic.mapper import IdentityMapper
from pymbolic.mapper.collector import TermCollector
from pymbolic.mapper.constant_folder import CommutativeConstantFoldingMapper
from pymbolic.typing import ArithmeticExpression, Expression


class DistributeMapper(IdentityMapper[[]]):
    """Example usage:

    .. doctest::

        >>> import pymbolic.primitives as p
        >>> x = p.Variable("x")
        >>> expr = (x+1)**7
        >>> from pymbolic.mapper.distributor import DistributeMapper as DM
        >>> print DM()(expr) # doctest: +SKIP
        7*x**6 + 21*x**5 + 21*x**2 + 35*x**3 + 1 + 35*x**4 + 7*x + x**7
    """

    def __init__(self, collector=None, const_folder=None) -> None:
        if collector is None:
            collector = TermCollector()
        if const_folder is None:
            const_folder = CommutativeConstantFoldingMapper()

        self.collector = collector
        self.const_folder = const_folder

    def collect(self, expr):
        return self.collector(self.const_folder(expr))

    def map_sum(self, expr):
        res = IdentityMapper.map_sum(self, expr)
        if isinstance(res, p.Sum):
            return self.collect(res)
        else:
            return res

    def map_product(self, expr: p.Product) -> Expression:
        def dist(prod):
            if not isinstance(prod, p.Product):
                return prod

            leading = []
            for i in prod.children:
                if isinstance(i, p.Sum):
                    break
                else:
                    leading.append(i)

            if len(leading) == len(prod.children):
                # no more sums found
                result = pymbolic.flattened_product(prod.children)
                return result
            else:
                sum = prod.children[len(leading)]
                assert isinstance(sum, p.Sum)
                rest = prod.children[len(leading)+1:]
                if rest:
                    rest = dist(p.Product(rest))
                else:
                    rest = 1

                result = self.collect(pymbolic.flattened_sum([
                       pymbolic.flattened_product(leading) * dist(sumchild*rest)
                       for sumchild in sum.children
                       ]))
                return result

        return dist(IdentityMapper.map_product(self, expr))

    def map_quotient(self, expr):
        if p.is_zero(expr.numerator - 1):
            return expr
        else:
            # not the smartest thing we can do, but at least *something*
            return pymbolic.flattened_product([
                    type(expr)(1, self.rec(expr.denominator)),
                    self.rec(expr.numerator)
                    ])

    def map_power(self, expr: p.Power) -> Expression:
        from pymbolic.primitives import Sum

        newbase = self.rec(expr.base)
        if isinstance(newbase, p.Product):
            return self.rec(pymbolic.flattened_product([
                cast(ArithmeticExpression, child)**expr.exponent
                    for child in newbase.children
                ]))

        if isinstance(expr.exponent, int):
            if isinstance(newbase, Sum):
                return self.rec(
                        pymbolic.flattened_product(
                            expr.exponent*(newbase,)))
            else:
                return IdentityMapper.map_power(self, expr)
        else:
            return IdentityMapper.map_power(self, expr)


def distribute(
            expr: Expression, parameters=None, commutative=True
        ) -> Expression:
    if parameters is None:
        parameters = frozenset()
    if commutative:
        return DistributeMapper(TermCollector(parameters))(expr)
    else:
        return DistributeMapper(lambda x: x)(expr)
