import tests




class Polynomial(object):
    def __init__(self, base, data):
        self.Base = base

        # list of (exponent, coefficient tuples)
        # sorted in increasing order
        # one entry per degree
        self.Data = data 
        
        # Remember the Zen, Luke: Sparse is better than dense.

    def __neg__(self):
        return Polynomial(self.Base,
                          [(exp, -coeff)
                           for (exp, coeff) in self.Data])

    def __add__(self, other):
        if not isinstance(other, Polynomial) or other.Base != self.Base:
            other = Polynomial(other, ((1,1),))

        iself = 0
        iother = 0

        result = []
        while iself < len(self.Data) and iother < len(other.Data):
            exp_self = self.Data[iself][0]
            exp_other = other.Data[iother][0]
            if exp_self == exp_other:
                coeff = self.Data[iself][1] + other.Data[iother][1]
                if not coeff:
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

        def sortkey((exp, coeff)): return exp
        result.sort(key=sortkey)

        uniq_result = []
        i = 0
        last_exp = None
        for exp, coeff in result:
            if last_exp == exp:
                newcoeff = uniq_result[-1][1]+coeff
                if newcoeff:
                    uniq_result.pop()
                else:
                    uniq_result[-1] = last_exp, newcoeff

            else:
                uniq_result.append((exp, coeff))
                last_exp = exp

        return Polynomial(self.Base, tuple(uniq_result))

    def __rmul__(self, other):
        return Polynomial(self.Base, [(exp, other * coeff)
                                      for exp, coeff in self.Data])

    def __pow__(self, other):
        n = int(other)
        if n < 0:
            raise RuntimeError, "negative powers of polynomials not defined"
        
        aux = Polynomial(self.Base, ((0, 1),))
        x = self

        # http://c2.com/cgi/wiki?IntegerPowerAlgorithm
        while n > 0:
            if n & 1:
                aux *= x
                if n == 1:
                    return aux
            x = x * x
            n //= 2
    
        return aux

    def __divmod__(self, other):
        pass

    def __str__(self):
        sbase = str(self.Base)
        def stringify_expcoeff((exp, coeff)):
            if exp == 1:
                if tests.is_one(coeff):
                    return sbase
                else:
                    return "%s*%s" % (str(coeff), sbase)
            elif exp == 0:
                return str(coeff)
            else:
                if tests.is_one(coeff):
                    return "%s**%s" % (sbase, exp) 
                else:
                    return "%s*%s**%s" % (str(coeff), sbase, exp) 

        return "(%s)" % " + ".join(stringify_expcoeff(i) for i in self.Data[::-1])

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name,
                               repr(self.Base), 
                               repr(self.Data))
        
    def __hash__(self):
        return hash(self.Base) ^ hash(self.Children)




if __name__ == "__main__":
    xpoly = Polynomial("x", ((0,1), (2,1)))
    ypoly = Polynomial("y", ((0,xpoly), (1,2), (2,-xpoly)))
    print xpoly**3
    print xpoly + 1
    print xpoly**3-xpoly
    print (xpoly*ypoly)**7
