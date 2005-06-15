class Polynomial(Expression):
    def __init__(self, base, coeff):
        self.Base = base

        # list of (exponent, coefficient tuples)
        # sorted in increasing order
        # one entry per degree
        self.Data = children 
        
        # Remember the Zen, Luke: Sparse is better than dense.

    def __neg__(self):
        return Polynomial(self.Base,
                          [(exp, -coeff)
                           for (exp, coeff) in self.Data])

    def __add__(self, other):
        if not isinstance(other, Polynomial) or other.Base != self.Base:
            return Expression.__add__(self, other)

        iself = 0
        iother = 0

        result = []
        while iself < len(self.Data) and iother < len(other.Data):
            exp_self = self.Data[iself][0]
            exp_other = other.Data[iother][0]
            if exp_self == exp_other:
                coeff = self.Data[iself][1] + other.Data[iother][1]
                if coeff != Constant(0):
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

        return Polynomial(self.Base, result)

    def __mul__(self, other):
        if not isinstance(other, Polynomial) or other.Base != self.Base:
            return Expression.__mul__(self, other)
        raise NotImplementedError

    def __hash__(self):
        return hash(self.Base) ^ hash(self.Children)

    def invoke_mapper(self, mapper):
        return mapper.map_polynomial(self)
