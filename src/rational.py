import pymbolic.traits as traits




class Rational(object):
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

    def __nonzero__(self):
        return bool(self.Numerator)

    def __neg__(self):
        return Rational(-self.Numerator, self.Denominator)

    def __add__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)

        t = traits.common_traits(self.Denominator, other.Denominator)
        newden = t.lcm(self.Denominator, other.Denominator)
        newnum = self.Numerator * newden/self.Denominator + \
                 other.Numerator * newden/other.Denominator
        gcd = t.gcd(newden, newnum)
        return Rational(newnum/gcd, newden/gcd)

    def __radd__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)

        t = traits.common_traits(self.Denominator, other.Denominator)
        newden = t.lcm(self.Denominator, other.Denominator)
        newnum = other.Numerator * newden/other.Denominator + \
                 self.Numerator * newden/self.Denominator
        gcd = t.gcd(newden, newnum)
        return Rational(newnum/gcd, newden/gcd)

    def __sub__(self, other):
        return self.__add__(other.__neg__())

    def __rsub__(self, other):
        return self.__neg__().__radd__(other)

    def __mul__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)

        t = traits.common_traits(self.Numerator, other.Numerator,
                                 self.Denominator, other. Denominator)
        gcd_1 = t.gcd(self.Numerator, other.Denominator)
        gcd_2 = t.gcd(other.Numerator, self.Denominator)

        return Rational(self.Numerator/gcd_1 * other.Numerator/gcd_2,
                        self.Denominator/gcd_2 * other.Denominator/gcd_1)

    def __rmul__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)

        t = traits.common_traits(self.Numerator, other.Numerator,
                                 self.Denominator, other. Denominator)
        gcd_1 = t.gcd(self.Numerator, other.Denominator)
        gcd_2 = t.gcd(other.Numerator, self.Denominator)

        return Rational(other.Numerator/gcd_2 * self.Numerator/gcd_1,
                        other.Denominator/gcd_1 * self.Denominator/gcd_2)

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

    def __str__(self):
        return "%s/%s" % (str(self.Numerator), str(self.Denominator))

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               repr(self.Numerator), repr(self.Denominator))

    def __float__(self):
        return float(self.Numerator) / flaot(self.Denominator)

    def __hash__(self):
        return 0xcafe ^ hash(self.Numerator) ^ hash(self.Denominator)




if __name__ == "__main__":
    one = Rational(1)
    print 3 + 1/(1 - 3/(one + 17))
    print one/3 + 2*one/3
    print one/3 + 2*one/3 + 0*one/1771
