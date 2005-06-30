def traits(x):
    try:
        return x.traits()
    except AttributeError:
        if isinstance(x, complex): return ComplexTraits
        if isinstance(x, float, int): return RealTraits
        raise NotImplementedError




def common_traits(*args):
    def common_traits_two(t_x, t_y):
        if isinstance(t_y, t_x.__class__):
            return t_y
        elif isinstance(t_x, t_y.__class__):
            return t_x
        else:
            raise RuntimeError, "No common traits type between '%s' and '%s'" % \
                  (t_x.__class__.__name__, t_y.__class__.__name__)

    return reduce(common_traits_two, (traits(arg) for arg in args))




class Traits:
    def one(self): raise NotImplementedError
    def zero(self): raise NotImplementedError




class EuclideanRingTraits(Traits):
    @staticmethod
    def norm(x):
        """Returns the algebraic norm of the element x.
 
        "Norm" is used as in the definition of a Euclidean ring,
        see [Bosch], p. 42
        """"
        """
        raise NotImplementedError

    @staticmethod
    def gcd_extended(q, r): 
        """Returns a tuple """
        raise NotImplementedError
 
    def gcd_extended(self, q, r): 
        """Returns a tuple """

    @staticmethod
    def gcd(self): 
        raise NotImplementedError

    @staticmethod
    def lcm(a, b): raise NotImplementedError

    @staticmethod
    def lcm_extended(a, b): raise NotImplementedError




class FieldTraits(Traits):
    pass

