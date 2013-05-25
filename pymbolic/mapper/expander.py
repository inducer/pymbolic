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

import pymbolic
from pymbolic.mapper import IdentityMapper
from pymbolic.mapper.collector import TermCollector
from pymbolic.primitives import \
        Sum, Product, Power, AlgebraicLeaf, \
        is_constant




class ExpandMapper(IdentityMapper):
    """Example usage:

    .. doctest::

        >>> import pymbolic.primitives as p
        >>> x = p.Variable("x")
        >>> expr = (x+1)**7
        >>> from pymbolic.mapper.expander import ExpandMapper as EM
        >>> print EM()(expr) # doctest: +SKIP
        7*x**6 + 21*x**5 + 21*x**2 + 35*x**3 + 1 + 35*x**4 + 7*x + x**7
    """

    def __init__(self, collector=TermCollector()):
        self.collector = collector

    def map_sum(self, expr):
        res = IdentityMapper.map_sum(self, expr)
        if isinstance(res, Sum):
            return self.collector(res)
        else:
            return res

    def map_product(self, expr):
        def expand(prod):
            if not isinstance(prod, Product):
                return prod

            leading = []
            for i in prod.children:
                if isinstance(i, Sum):
                    break
                else:
                    leading.append(i)

            if len(leading) == len(prod.children):
                # no more sums found
                result = pymbolic.flattened_product(prod.children)
                return result
            else:
                sum = prod.children[len(leading)]
                assert isinstance(sum, Sum)
                rest = prod.children[len(leading)+1:]
                if rest:
                    rest = expand(Product(rest))
                else:
                    rest = 1

                result = self.collector(pymbolic.flattened_sum(
                       pymbolic.flattened_product(leading) * expand(sumchild*rest)
                       for sumchild in sum.children
                       ))
                return result

        return expand(IdentityMapper.map_product(self, expr))

    def map_quotient(self, expr):
        raise NotImplementedError

    def map_power(self, expr):
        from pymbolic.primitives import Expression, Sum

        if isinstance(expr.base, Product):
            return self.rec(pymbolic.flattened_product(
                child**expr.exponent for child in newbase))

        if isinstance(expr.exponent, int):
            newbase = self.rec(expr.base)
            if isinstance(newbase, Sum):
                return self.map_product(pymbolic.flattened_product(expr.exponent*(newbase,)))
            else:
                return IdentityMapper.map_power(self, expr)
        else:
            return IdentityMapper.map_power(self, expr)




def expand(expr, parameters=set(), commutative=True):
    if commutative:
        return ExpandMapper(TermCollector(parameters))(expr)
    else:
        return ExpandMapper(lambda x: x)(expr)
