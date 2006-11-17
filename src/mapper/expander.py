import pymbolic
from pymbolic.mapper import IdentityMapper
from pymbolic.primitives import Sum, Product, Power, AlgebraicLeaf




class CommutativeTermCollector(object):
    """A term collector that assumes that multiplication is commutative.
    """

    def __init__(self, parameters=set()):
        self.Parameters = parameters

    def split_term(self, mul_term):
        """Returns  a pair consisting of:
        - a frozenset of (base, exponent) pairs
        - a product of coefficients (i.e. constants and parameters)
        
        The set takes care of order-invariant comparison for us and is hashable.

        The argument `product' has to be fully expanded already.
        """
        from pymbolic import get_dependencies


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
            if  get_dependencies(term) <= self.Parameters:
                coefficients.append(term)
            else:
                cleaned_base2exp[base] = exp

        term = frozenset((base,exp) for base, exp in cleaned_base2exp.iteritems())
        return term, pymbolic.product(coefficients)

    def __call__(self, mysum):
        assert isinstance(mysum, Sum)

        term2coeff = {}
        for child in mysum.children:
            term, coeff = self.split_term(child)
            if term in term2coeff:
                term2coeff[term] += coeff
            else:
                term2coeff[term] = coeff

        def rep2term(rep):
            return pymbolic.product(base**exp for base, exp in rep)

        result = pymbolic.sum(coeff*rep2term(termrep) 
                for termrep, coeff in term2coeff.iteritems())
        return result




class ExpandMapper(IdentityMapper):
    def __init__(self, collector=CommutativeTermCollector()):
        self.Collector = collector
    
    def map_product(self, expr):
        from pymbolic.primitives import Sum

        def expand(children):
            leading = []
            for i in children:
                if isinstance(i, Sum):
                    break
                else:
                    leading.append(i)

            if len(leading) == len(children):
                # no more sums found
                result = pymbolic.product(children)
                return result
            else:
                sum = children[len(leading)]
                assert isinstance(sum, Sum)
                rest = children[len(leading)+1:]

                result = self.Collector(pymbolic.sum(
                       expand(leading+[sumchild]+rest)
                       for sumchild in sum.children))
                return result

        return expand([self.rec(child) for child in expr.children])

    def map_quotient(self, expr):
        raise NotImplementedError

    def map_power(self, expr):
        from pymbolic.primitives import Expression, Sum

        if isinstance(expr.base, Product):
            return self.rec(pymbolic.product(
                child**expr.exponent for child in newbase))

        if isinstance(expr.exponent, int):
            newbase = self.rec(expr.base)
            if isinstance(newbase, Sum):
                return self.map_product(pymbolic.product(expr.exponent*(newbase,)))
            else:
                return IdentitityMapper.map_power(expr)
        else:
            return IdentitityMapper.map_power(expr)




def expand(expr):
    return ExpandMapper()(expr)
