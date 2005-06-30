import rational
import traits




def _int_or_ni(x):
    if x is NotImplemented:
        return x
    else:
        return Integer(x)




class Integer(int):
    def traits(self):
        return IntegerTraits()

    def __add__(self, other): return _int_or_ni(int.__add__(self, other))
    def __sub__(self, other): return _int_or_ni(int.__sub__(self, other))
    def __mul__(self, other): return _int_or_ni(int.__mul__(self, other))
    def __floordiv__(self, other): return _int_or_ni(int.__floordiv__(self, other))
    def __mod__(self, other): return _int_or_ni(int.__mod__(self, other))
    def __pow__(self, other): return _int_or_ni(int.__pow__(self, other))

    def __truediv__(self, other):
        if self % other != 0:
            return rational.Rational(self, other)
        else:
            return super.__truediv__(self, other)

    __div__ = __truediv__

    def __radd__(self, other): return _int_or_ni(int.__radd__(self, other))
    def __rsub__(self, other): return _int_or_ni(int.__rsub__(self, other))
    def __rmul__(self, other): return _int_or_ni(int.__rmul__(self, other))
    def __rfloordiv__(self, other): return _int_or_ni(int.__rfloordiv__(self, other))
    def __rmod__(self, other): return _int_or_ni(int.__rmod__(self, other))
    def __rpow__(self, other): return _int_or_ni(int.__rpow__(self, other))

    def __neg__(self, other): return Integer(int.__neg__(self))

    def __rtruediv__(self, other):
        if other % self != 0:
            return rational.Rational(other, self)
        else:
            return int.__rtruediv__(self, other)

    __rdiv__ = __rtruediv__




class IntegerTraits(traits.EuclideanRingTraits):
    def norm(self, x):
        return abs(x)
