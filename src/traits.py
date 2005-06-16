def traits(x):
    try:
        return x.traits
    except AttributeError:
        if isinstance(x, complex): return ComplexTraits
        if isinstance(x, float): return FloatTraits
        if isinstance(x, int): return IntegerTraits
        return NotImplementedError




def most_special_traits(x, y):
    t_x = traits(x)
    t_y = traits(y)

    if isinstance(t_y, t_x.__class__):
        return t_y
    else:
        return t_x
    



class Traits:
    def one(self): raise NotImplementedError
    def zero(self): raise NotImplementedError

    def degree(self, x):
        """Returns the degree of the element x.

        "Degree" is used as in the definition of a Euclidean ring,
        see [Bosch], p. 42
        """"
        raise NotImplementedError

    def gcd_extended(self, q, r): 
        """Returns a tuple 

    def gcd(self): raise NotImplementedError
    def lcm(self): raise NotImplementedError
    def lcm_extended(self): raise NotImplementedError
