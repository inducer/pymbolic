import pymbolic
from pymbolic.mapper import IdentityMapper




class TermCollector(IdentityMapper):
    """A term collector that assumes that multiplication is commutative.
    """

    def __init__(self, parameters=set()):
        self.parameters = parameters

    def get_dependencies(self, expr):
        from pymbolic.mapper.dependency import DependencyMapper
        return DependencyMapper()(expr)

    def split_term(self, mul_term):
        """Returns  a pair consisting of:
        - a frozenset of (base, exponent) pairs
        - a product of coefficients (i.e. constants and parameters)
        
        The set takes care of order-invariant comparison for us and is hashable.

        The argument `product' has to be fully expanded already.
        """
        from pymbolic.primitives import Product, Power, AlgebraicLeaf

        def base(term):
            if isinstance(term, Power):
                return term.base
            else:
                return term

        def exponent(term):
            if isinstance(term, Power):
                return term.exponent
            else:
                return 1

        if isinstance(mul_term, Product):
            terms = mul_term.children
        elif isinstance(mul_term, (Power, AlgebraicLeaf)):
            terms = [mul_term]
        elif not bool(self.get_dependencies(mul_term)):
            terms = [mul_term]
        else:
            raise RuntimeError, "split_term expects a multiplicative term"

        base2exp = {}
        for term in terms:
            mybase = base(term)
            myexp = exponent(term)

            if mybase in base2exp:
                base2exp[mybase] += myexp
            else:
                base2exp[mybase] = myexp

        coefficients = []
        cleaned_base2exp = {}
        for base, exp in base2exp.iteritems():
            term = base**exp
            if  self.get_dependencies(term) <= self.parameters:
                coefficients.append(term)
            else:
                cleaned_base2exp[base] = exp

        term = frozenset((base,exp) for base, exp in cleaned_base2exp.iteritems())
        return term, pymbolic.flattened_product(coefficients)

    def map_sum(self, mysum):
        term2coeff = {}
        for child in mysum.children:
            term, coeff = self.split_term(child)
            term2coeff[term] = term2coeff.get(term, 0) + coeff

        def rep2term(rep):
            return pymbolic.flattened_product(base**exp for base, exp in rep)

        result = pymbolic.flattened_sum(coeff*rep2term(termrep) 
                for termrep, coeff in term2coeff.iteritems())
        return result
