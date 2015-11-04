from __future__ import division
from __future__ import absolute_import
import six

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


class TermCollector(IdentityMapper):
    """A term collector that assumes that multiplication is commutative.

    Allows specifying *parameters* (a set of
    :class:`pymbolic.primitive.Variable` instances) that are viewed as being
    coefficients and are not used for term collection.
    """

    def __init__(self, parameters=set()):
        self.parameters = parameters

    def get_dependencies(self, expr):
        from pymbolic.mapper.dependency import DependencyMapper
        return DependencyMapper()(expr)

    def split_term(self, mul_term):
        """Returns  a pair consisting of:
        - a frozenset of (base, exponent) pairs
        - a product of coefficients (i.e. constants and parameters)

        The set takes care of order-invariant comparison for us and is hashable.

        The argument `product' has to be fully expanded already.
        """
        from pymbolic.primitives import Product, Power, AlgebraicLeaf

        def base(term):
            if isinstance(term, Power):
                return term.base
            else:
                return term

        def exponent(term):
            if isinstance(term, Power):
                return term.exponent
            else:
                return 1

        if isinstance(mul_term, Product):
            terms = mul_term.children
        elif isinstance(mul_term, (Power, AlgebraicLeaf)):
            terms = [mul_term]
        elif not bool(self.get_dependencies(mul_term)):
            terms = [mul_term]
        else:
            raise RuntimeError("split_term expects a multiplicative term")

        base2exp = {}
        for term in terms:
            mybase = base(term)
            myexp = exponent(term)

            if mybase in base2exp:
                base2exp[mybase] += myexp
            else:
                base2exp[mybase] = myexp

        coefficients = []
        cleaned_base2exp = {}
        for base, exp in six.iteritems(base2exp):
            term = base**exp
            if self.get_dependencies(term) <= self.parameters:
                coefficients.append(term)
            else:
                cleaned_base2exp[base] = exp

        term = frozenset(
                (base, exp) for base, exp in six.iteritems(cleaned_base2exp))
        return term, self.rec(pymbolic.flattened_product(coefficients))

    def map_sum(self, mysum):
        term2coeff = {}
        for child in mysum.children:
            term, coeff = self.split_term(child)
            term2coeff[term] = term2coeff.get(term, 0) + coeff

        def rep2term(rep):
            return pymbolic.flattened_product(base**exp for base, exp in rep)

        result = pymbolic.flattened_sum(coeff*rep2term(termrep)
                for termrep, coeff in six.iteritems(term2coeff))
        return result
