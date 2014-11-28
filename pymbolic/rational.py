from __future__ import division, absolute_import, print_function

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

from six.moves import intern
import pymbolic.primitives as primitives
import pymbolic.traits as traits


class Rational(primitives.Expression):
    def __init__(self, numerator, denominator=1):
        d_unit = traits.traits(denominator).get_unit(denominator)
        numerator /= d_unit
        denominator /= d_unit
        self.Numerator = numerator
        self.Denominator = denominator

    def _num(self):
        return self.Numerator
    numerator = property(_num)

    def _den(self):
        return self.Denominator
    denominator = property(_den)

    def __bool__(self):
        return bool(self.Numerator)

    __nonzero__ = __bool__

    def __neg__(self):
        return Rational(-self.Numerator, self.Denominator)

    def __eq__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)

        return self.Numerator == other.Numerator and \
               self.Denominator == other.Denominator

    def __add__(self, other):
        if not isinstance(other, Rational):
            newother = Rational(other)
        else:
            newother = other

        try:
            t = traits.common_traits(self.Denominator, newother.Denominator)
            newden = t.lcm(self.Denominator, newother.Denominator)
            newnum = self.Numerator * newden/self.Denominator + \
                     newother.Numerator * newden/newother.Denominator
            gcd = t.gcd(newden, newnum)
            return primitives.quotient(newnum/gcd, newden/gcd)
        except traits.NoTraitsError:
            return primitives.Expression.__add__(self, other)
        except traits.NoCommonTraitsError:
            return primitives.Expression.__add__(self, other)

    __radd__ = __add__

    def __sub__(self, other):
        return self.__add__(-other)

    def __rsub__(self, other):
        return (-self).__radd__(other)

    def __mul__(self, other):
        if not isinstance(other, Rational):
            newother = Rational(other)

        try:
            t = traits.common_traits(self.Numerator, newother.Numerator,
                                     self.Denominator, newother. Denominator)
            gcd_1 = t.gcd(self.Numerator, newother.Denominator)
            gcd_2 = t.gcd(newother.Numerator, self.Denominator)

            new_num = self.Numerator/gcd_1 * newother.Numerator/gcd_2
            new_denom = self.Denominator/gcd_2 * newother.Denominator/gcd_1

            if not (new_denom-1):
                return new_num

            return Rational(new_num, new_denom)
        except traits.NoTraitsError:
            return primitives.Expression.__mul__(self, other)
        except traits.NoCommonTraitsError:
            return primitives.Expression.__mul__(self, other)

    __rmul__ = __mul__

    def __div__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)

        return self.__mul__(Rational(other.Denominator, other.Numerator))

    def __rdiv__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)

        return Rational(self.Denominator, self.Numerator).__rmul__(other)

    def __pow__(self, other):
        return Rational(self.Denominator**other, self.Numerator**other)

    def __getinitargs__(self):
        return (self.Numerator, self.Denominator)

    def reciprocal(self):
        return Rational(self.Denominator, self.Numerator)

    mapper_method = intern("map_rational")


if __name__ == "__main__":
    one = Rational(1)
    print(3 + 1/(1 - 3/(one + 17)))
    print(one/3 + 2*one/3)
    print(one/3 + 2*one/3 + 0*one/1771)
