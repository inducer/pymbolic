from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from six.moves import range, intern

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

import pymbolic
from pymbolic.primitives import Expression
import pymbolic.algorithm as algorithm
from pymbolic.traits import traits, EuclideanRingTraits, FieldTraits




def _sort_uniq(data):
    def sortkey(xxx_todo_changeme): (exp, coeff) = xxx_todo_changeme; return exp
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




class LexicalMonomialOrder:
    def __call__(self, a, b):
        from pymbolic.primitives import Variable
        # is a < b?
        assert isinstance(a, Variable) and isinstance(b, Variable)
        return a.name < b.name

    def __eq__(self, other):
        return isinstance(other, LexicalMonomialOrder)

    def __repr__(self):
        return "LexicalMonomialOrder()"





class Polynomial(Expression):
    def __init__(self, base, data=None, unit=1, var_less=LexicalMonomialOrder()):
        self.Base = base
        self.Unit = unit
        self.VarLess = var_less

        # list of (exponent, coefficient tuples)
        # sorted in increasing order
        # one entry per degree
        if data is None:
            self.Data = ((1, unit),)
        else:
            self.Data = tuple(data)

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
        if not other:
            return self

        if not isinstance(other, Polynomial):
            other = Polynomial(self.Base, ((0, other),))

        if other.Base != self.Base:
            assert self.VarLess == other.VarLess

            if self.VarLess(self.Base, other.Base):
                other = Polynomial(self.Base, ((0, other),))
            else:
                return other.__add__(self)

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
        if not isinstance(other, Polynomial):
            if other == self.Base:
                other = Polynomial(self.Base)
            else:
                return Polynomial(self.Base, [(exp, coeff * other)
                                              for exp, coeff in self.Data])

        if other.Base != self.Base:
            assert self.VarLess == other.VarLess

            if self.VarLess(self.Base, other.Base):
                return Polynomial(self.Base, [(exp, coeff * other)
                                              for exp, coeff in self.Data])
            else:
                return other.__mul__(self)

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
        if not isinstance(other, Polynomial):
            dm_list = [(exp, divmod(coeff, other)) for exp, coeff in self.Data]
            return Polynomial(self.Base, [(exp, quot) for (exp, (quot, rem)) in dm_list]),\
                   Polynomial(self.Base, [(exp, rem) for (exp, (quot, rem)) in dm_list])

        if other.Base != self.Base:
            assert self.VarLess == other.VarLess

            if self.VarLess(self.Base, other.Base):
                dm_list = [(exp, divmod(coeff, other)) for exp, coeff in self.Data]
                return Polynomial(self.Base, [(exp, quot) for (exp, (quot, rem)) in dm_list]),\
                        Polynomial(self.Base, [(exp, rem) for (exp, (quot, rem)) in dm_list])
            else:
                other_unit = Polynomial(other.Base, ((0,other.unit),), self.VarLess)
                quot, rem = divmod(other_unit, other)
                return quot * self, rem * self

        if other.degree == -1:
            raise DivisionByZeroError

        quot = Polynomial(self.Base, ())
        rem = self
        other_lead_coeff = other.Data[-1][1]
        other_lead_exp = other.Data[-1][0]


        coeffs_are_field = isinstance(traits(self.Unit), FieldTraits)
        from pymbolic.primitives import quotient
        while rem.degree >= other.degree:
            if coeffs_are_field:
                coeff_factor = quotient(rem.Data[-1][1], other_lead_coeff)
            else:
                coeff_factor, lead_rem = divmod(rem.Data[-1][1], other_lead_coeff)
                if lead_rem:
                    return quot, rem
            deg_diff = rem.Data[-1][0] - other_lead_exp

            this_fac = Polynomial(self.Base, ((deg_diff, coeff_factor),))
            quot += this_fac
            rem -= this_fac * other
        return quot, rem

    def __div__(self, other):
        if not isinstance(other, Polynomial):
            return 1/other * self
        q, r = divmod(self, other)
        if r.degree != -1:
            raise ValueError("division yielded a remainder")
        return q

    __truediv__ = __div__

    def __floordiv__(self):
        return self.__divmod__(self, other)[0]

    def __mod__(self):
        return self.__divmod__(self, other)[1]

    def _data(self):
        return self.Data
    data = property(_data)

    def _base(self):
        return self.Base
    base = property(_base)

    def _unit(self):
        return self.Unit
    unit = property(_unit)

    def _degree(self):
        try:
            return self.Data[-1][0]
        except IndexError:
            return -1
    degree = property(_degree)

    def __getinitargs__(self):
        return (self.Base, self.Data, self.Unit, self.VarLess)

    mapper_method = intern("map_polynomial")

    def as_primitives(self):
        deps = pymbolic.get_dependencies(self)
        context = dict((dep, dep) for dep in deps)
        return pymbolic.evaluate(self, context)

    def get_coefficient(self, sought_exp):
        # FIXME use bisection
        for exp, coeff in self.Data:
            if exp == sought_exp:
                return coeff
        return 0




def from_primitives(expr, var_order):
    from pymbolic import get_dependencies, evaluate

    deps = get_dependencies(expr)
    var_deps = [dep for dep in deps if dep in var_order]
    context = dict((vd, Polynomial(vd, var_order=var_order))
            for vd in var_deps)

    # FIXME not fast, but works
    # (and exercises multivariate polynomial code)
    return evaluate(expr, context)




def differentiate(poly):
    return Polynomial(
        poly.base,
        tuple((exp-1, exp*coeff)
              for exp, coeff in poly.data
              if not exp == 0))



def integrate(poly):
    return Polynomial(
        poly.base,
        tuple((exp+1, pymbolic.quotient(poly.unit, (exp+1))*coeff)
              for exp, coeff in poly.data))




def integrate_definite(poly, a, b):
    antideriv = integrate(poly)
    a_bound = pymbolic.substitute(antideriv, {poly.base: a})
    b_bound = pymbolic.substitute(antideriv, {poly.base: b})

    return pymbolic.sum((b_bound, -a_bound))




def leading_coefficient(poly):
    return poly.data[-1][1]




def general_polynomial(base, coefflist, degree):
    return Polynomial(base,
            ((i, coefflist[i]) for i in range(degree+1)))




class PolynomialTraits(EuclideanRingTraits):
    @staticmethod
    def norm(x):
        return x.degree

    @staticmethod
    def get_unit(x):
        lc = leading_coefficient(x)
        return traits(lc).get_unit(lc)




if __name__ == "__main__":
    x = Polynomial(pymbolic.var("x"))
    y = Polynomial(pymbolic.var("y"))

    u = (x+1)**5
    v = pymbolic.evaluate_kw(u, x=x)
    print(u)
    print(v)

    if False:
        # NOT WORKING INTRODUCE TESTS
        u = (x+y)**5
        v = x+y
        #u = x+1
        #v = 3*x+1
        q, r = divmod(u, v)
        print(q, "R", r)
        print(q*v)
        print("REASSEMBLY:", q*v + r)


