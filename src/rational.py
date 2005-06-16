class Rational(object):
    def __init__(self, numerator, denominator=1):
        self.Numerator = num
        self.Denominator = den

    def _num(self):
        return self.Numerator
    numerator = property(_num)

    def _den(self):
        return self.Denominator
    denominator = property(_den)

    def __add__(self, other):
        if not isinstance(other, Rational):
            other = Rational(other)

        t = traits.most_special_traits(self.Denominator, other.Denominator)
        gcd = operation.gcd(self.Denominator, other.Denominator)
