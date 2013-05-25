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

import cmath
from pytools import memoize




def integer_power(x, n, one=1):
    """Compute :math:`x^n` using only multiplications.

    See also the `C2 wiki <http://c2.com/cgi/wiki?IntegerPowerAlgorithm>`_.
    """

    assert isinstance(n, int)

    if n < 0:
        raise RuntimeError("the integer power algorithm does not work for negative numbers")

    aux = one

    while n > 0:
        if n & 1:
            aux *= x
            if n == 1:
                return aux
        x = x * x
        n //= 2



def gcd(q, r):
    return extended_euclidean(q, r)[0]

def gcd_many(*args):
    if len(args) == 0:
        return 1
    elif len(args) == 1:
        return args[0]
    else:
        return reduce(gcd, args)

def lcm(q, r):
    return abs(q*r)//gcd(q, r)




def extended_euclidean(q, r):
    """Return a tuple *(p, a, b)* such that :math:`p = aq + br`,
    where *p* is the greatest common divisor of *q* and *r*.

    See also the `Wikipedia article on the Euclidean algorithm <https://en.wikipedia.org/wiki/Euclidean_algorithm>`_.
    """
    import pymbolic.traits as traits

    # see [Davenport], Appendix, p. 214

    t = traits.common_traits(q, r)

    if t.norm(q) < t.norm(r):
        p, a, b = extended_euclidean(r, q)
        return p, b, a

    Q = 1, 0
    R = 0, 1

    while r:
        quot, t = divmod(q, r)
        T = Q[0] - quot*R[0], Q[1] - quot*R[1]
        q, r = r, t
        Q, R = R, T

    return q, Q[0], Q[1]





@memoize
def find_factors(N):
    from math import sqrt

    N1 = 2
    max_N1 = int(sqrt(N))+1
    while N % N1 != 0 and N1 <= max_N1:
        N1 += 1

    if N1 > max_N1:
        N1 = N

    N2 = N // N1

    return N1, N2




def fft(x, sign=1, wrap_intermediate=lambda x: x):
    r"""Computes the Fourier transform of x:

    .. math::

        F[x]_k = \sum_{j=0}^{n-1} z^{kj} x_j

    where :math:`z = \exp(-2i\pi\operatorname{sign}/n)` and ``n == len(x)``.
    Works for all positive *n*.

    See also `Wikipedia <http://en.wikipedia.org/wiki/Cooley-Tukey_FFT_algorithm>`_.
    """

    # revision 293076305, http://is.gd/1c7PI

    from math import pi
    import numpy

    N = len(x)

    if N == 1:
        return x

    N1, N2 = find_factors(N)

    sub_ffts = [
            wrap_intermediate(
                fft(x[n1::N1], sign, wrap_intermediate)
                * numpy.exp(numpy.linspace(0, sign*(-2j)*pi*n1/N1, N2,
                    endpoint=False)))
            for n1 in range(N1)]

    return numpy.hstack([
        sum(subvec * cmath.exp(sign*(-2j)*pi*n1*k1/N1)
            for n1, subvec in enumerate(sub_ffts))
        for k1 in range(N1)
        ])




def ifft(x, wrap_intermediate=lambda x:x):
    return (1/len(x))*fft(x, -1, wrap_intermediate)





def sym_fft(x, sign=1):
    """Perform a (symbolic) FFT on the :mod:`numpy` object array x.

    Remove near-zero floating point constants, insert
    :class:`pymbolic.primitives.CommonSubexpression` 
    wrappers at opportune points.
    """

    from pymbolic.mapper import IdentityMapper, CSECachingMapperMixin
    class NearZeroKiller(CSECachingMapperMixin, IdentityMapper):
        map_common_subexpression_uncached = \
                IdentityMapper.map_common_subexpression

        def map_constant(self, expr):
            if isinstance(expr, complex):
                r = expr.real
                i = expr.imag
                if abs(r) < 1e-15:
                    r = 0
                if abs(i) < 1e-15:
                    i = 0
                if i == 0:
                    return r
                else:
                    return complex(r, i)
            else:
                return expr

    import numpy

    def wrap_intermediate(x):
        if len(x) > 1:
            from pymbolic.primitives import CommonSubexpression
            result = numpy.empty(len(x), dtype=object)
            for i, x_i in enumerate(x):
                result[i] = CommonSubexpression(x_i)
            return result
        else:
            return x

    return NearZeroKiller()(
            fft(wrap_intermediate(x), sign=sign, wrap_intermediate=wrap_intermediate))






def csr_matrix_multiply(S, x):
    """Multiplies a :class:`scipy.sparse.csr_matrix` S by an object-array vector x.
    """
    h, w = S.shape

    import numpy
    result = numpy.empty_like(x)

    for i in xrange(h):
        result[i] = sum(S.data[idx]*x[S.indices[idx]] 
                for idx in range(S.indptr[i], S.indptr[i+1]))

    return result




if __name__ == "__main__":
    import integer
    q = integer.Integer(14)
    r = integer.Integer(22)
    gcd, a, b = extended_euclidean(q, r)
    print gcd, "=", a, "*", q, "+", b, "*", r
    print a*q + b*r
