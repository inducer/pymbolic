import algorithm




class NoTraitsError(Exception):
    pass

class NoCommonTraitsError(Exception):
    pass




def traits(x):
    try:
        return x.traits()
    except AttributeError:
        if isinstance(x, (complex, float)): return FieldTraits()
        if isinstance(x, int): return IntegerTraits()
        raise NoTraitsError




def common_traits(*args):
    def common_traits_two(t_x, t_y):
        if isinstance(t_y, t_x.__class__):
            return t_y
        elif isinstance(t_x, t_y.__class__):
            return t_x
        else:
            raise NoCommonTraitsError, \
                  "No common traits type between '%s' and '%s'" % \
                  (t_x.__class__.__name__, t_y.__class__.__name__)

    return reduce(common_traits_two, (traits(arg) for arg in args))




class Traits(object):
    pass




class IntegralDomainTraits(Traits):
    pass




class EuclideanRingTraits(IntegralDomainTraits):
    @classmethod
    def norm(cls, x):
        """Returns the algebraic norm of the element x.
 
        "Norm" is used as in the definition of a Euclidean ring,
        see [Bosch], p. 42
        """
        raise NotImplementedError

    @staticmethod
    def gcd_extended(q, r): 
        """Return a tuple (p, a, b) such that p = aq + br, 
        where p is the greatest common divisor.
        """
        return algorithm.extended_euclidean(q, r)
 
    @staticmethod
    def gcd(q, r): 
        """Returns the greatest common divisor of q and r.
        """
        return algorithm.extended_euclidean(q, r)[0]

    @classmethod
    def lcm(cls, a, b):
        """Returns the least common multiple of a and b.
        """
        return a * b / cls.gcd(a, b)

    @staticmethod
    def get_unit(x):
        """Returns the unit in the prime factor decomposition of x.
        """
        raise NotImplementedError




class FieldTraits(IntegralDomainTraits):
    pass




class IntegerTraits(EuclideanRingTraits):
    @staticmethod
    def norm(x):
        return abs(x)

    @staticmethod
    def get_unit(x):
        if x < 0:
            return -1
        elif x > 0:
            return 1
        else:
            raise RuntimeError, "0 does not have a prime factor decomposition"

