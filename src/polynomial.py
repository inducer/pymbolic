from __future__ import division
import pymbolic.algorithm as algorithm
import pymbolic.traits as traits




def _sort_uniq(data):
    def sortkey((exp, coeff)): return exp
    data.sort(key=sortkey)
    
    uniq_result = []
    i = 0
    last_exp = None
    for exp, coeff in data:
        if last_exp == exp:
            newcoeff = uniq_result[-1][1]+coeff
            if not newcoeff:
                uniq_result.pop()
            else:
                uniq_result[-1] = last_exp, newcoeff

        else:
            uniq_result.append((exp, coeff))
            last_exp = exp
    return uniq_result




class Polynomial(object):
    def __init__(self, base, data = ((1,1),)):
        self.Base = base

        # list of (exponent, coefficient tuples)
        # sorted in increasing order
        # one entry per degree
        self.Data = data 
        
        # Remember the Zen, Luke: Sparse is better than dense.

    def coefficients(self):
        return [coeff for (exp, coeff) in self.Data]

    def traits(self):
        return PolynomialTraits()

    def __nonzero__(self):
        return len(self.Data) != 0

    def __eq__(self, other):
        return isinstance(other, Polynomial) \
               and (self.Base == other.Base) \
               and (self.Data == other.Data)
    def __ne__(self, other):
        return not self.__eq__(other)

    def __neg__(self):
        return Polynomial(self.Base,
                          [(exp, -coeff)
                           for (exp, coeff) in self.Data])

    def __add__(self, other):
        if not isinstance(other, Polynomial) or other.Base != self.Base:
            other = Polynomial(self.Base, ((0, other),))

        iself = 0
        iother = 0

        result = []
        while iself < len(self.Data) and iother < len(other.Data):
            exp_self = self.Data[iself][0]
            exp_other = other.Data[iother][0]
            if exp_self == exp_other:
                coeff = self.Data[iself][1] + other.Data[iother][1]
                if coeff:
                    result.append((exp_self, coeff))
                iself += 1
                iother += 1
            elif exp_self > exp_other:
                result.append((exp_other, other.Data[iother][1]))
                iother += 1
            elif exp_self < exp_other:
                result.append((exp_self, self.Data[iself][1]))
                iself += 1

        # we have exhausted at least one list, exhaust the other
        while iself < len(self.Data):
            exp_self = self.Data[iself][0]
            result.append((exp_self, self.Data[iself][1]))
            iself += 1
                
        while iother < len(other.Data):
            exp_other = other.Data[iother][0]
            result.append((exp_other, other.Data[iother][1]))
            iother += 1

        return Polynomial(self.Base, tuple(result))

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        return self+(-other)

    def __rsub__(self, other):
        return (-other)+self

    def __mul__(self, other):
        if not isinstance(other, Polynomial) or other.Base != self.Base:
            return Polynomial(self.Base, [(exp, coeff * other)
                                          for exp, coeff in self.Data])

        result = []

        for s_exp, s_coeff in self.Data:
            for o_exp, o_coeff in other.Data:
                result.append((s_exp+o_exp, s_coeff*o_coeff))

        return Polynomial(self.Base, tuple(_sort_uniq(result)))

    def __rmul__(self, other):
        return Polynomial(self.Base, [(exp, other * coeff)
                                      for exp, coeff in self.Data])

    def __pow__(self, other):
        return algorithm.integer_power(self, int(other),
                                       Polynomial(self.Base, ((0, 1),)))

    def __divmod__(self, other):
        if not isinstance(other, Polynomial) or other.Base != self.Base:
            dm_list = [(exp, divmod(coeff * other)) for exp, coeff in self.Data]
            return Polynomial(self.Base, [(exp, quot) for (exp, (quot, rem)) in dm_list]),\
                   Polynomial(self.Base, [(exp, rem) for (exp, (quot, rem)) in dm_list])

        if other.degree == -1:
            raise DivisionByZeroError

        quotient = Polynomial(self.Base, ())
        remainder = self
        other_lead_coeff = other.Data[-1][1]
        other_lead_exp = other.Data[-1][0]
        while remainder.degree >= other.degree:
            coeff_factor = remainder.Data[-1][1] / other_lead_coeff
            deg_diff = remainder.Data[-1][0] - other_lead_exp

            this_fac = Polynomial(self.Base, ((deg_diff, coeff_factor),))
            quotient += this_fac
            remainder -= this_fac * other
        return quotient, remainder

    def __div__(self):
        q, r = self.__divmod__(self, other)
        if r.degree != -1:
            raise ValueError, "division yielded a remainder"
        return q

    __truediv__ = __div__

    def __floordiv__(self):
        return self.__divmod__(self, other)[0]

    def __mod__(self):
        return self.__divmod__(self, other)[1]

    def __str__(self):
        sbase = str(self.Base)
        def stringify_expcoeff((exp, coeff)):
            if exp == 1:
                if not (coeff-1):
                    return sbase
                else:
                    return "%s*%s" % (str(coeff), sbase)
            elif exp == 0:
                return str(coeff)
            else:
                if not (coeff-1):
                    return "%s**%s" % (sbase, exp) 
                else:
                    return "%s*%s**%s" % (str(coeff), sbase, exp) 

        return "(%s)" % " + ".join(stringify_expcoeff(i) for i in self.Data[::-1])

    def _data(self):
        return self.Data
    data = property(_data)

    def _base(self):
        return self.Base
    base = property(_base)

    def _degree(self):
        try:
            return self.Data[-1][0]
        except IndexError:
            return -1
    degree = property(_degree)

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__,
                               repr(self.Base), 
                               repr(self.Data))
        
    def __hash__(self):
        return hash(self.Base) ^ hash(self.Children)




def derivative(poly):
    return Polynomial(
        poly.base,
        tuple((exp-1, exp*coeff)
              for exp, coeff in poly.data
              if not exp == 0))



def leading_coefficient(poly):
    return poly.data[-1][1]




class PolynomialTraits(traits.EuclideanRingTraits):
    @staticmethod
    def norm(x):
        return x.degree
    
    @staticmethod
    def get_unit(x):
        lc = leading_coefficient(x)
        return traits.traits(lc).get_unit(lc)



   
if __name__ == "__main__":
    x = Polynomial("x")
    y = Polynomial("y")
    xpoly = x**2 + 1
    ypoly = -y**2*xpoly + xpoly
    print xpoly
    print ypoly
    u = xpoly*ypoly
    print u
    print u**18
    print

    print 3*xpoly**3 + 1
    print xpoly 
    q,r = divmod(3*xpoly**3 + 1, xpoly)
    print q, r

