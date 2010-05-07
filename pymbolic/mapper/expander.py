import pymbolic
from pymbolic.mapper import IdentityMapper
from pymbolic.mapper.collector import TermCollector
from pymbolic.primitives import \
        Sum, Product, Power, AlgebraicLeaf, \
        is_constant




class ExpandMapper(IdentityMapper):
    def __init__(self, collector=TermCollector()):
        self.collector = collector
    
    def map_sum(self, expr):
        from pymbolic.primitives import Sum
        res = IdentityMapper.map_sum(self, expr)
        if isinstance(res, Sum):
            return self.collector(res)
        else:
            return res

    def map_product(self, expr):
        from pymbolic.primitives import Sum, Product

        def expand(prod):
            if not isinstance(prod, Product):
                return prod

            leading = []
            for i in prod.children:
                if isinstance(i, Sum):
                    break
                else:
                    leading.append(i)

            if len(leading) == len(prod.children):
                # no more sums found
                result = pymbolic.flattened_product(prod.children)
                return result
            else:
                sum = prod.children[len(leading)]
                assert isinstance(sum, Sum)
                rest = prod.children[len(leading)+1:]
                if rest:
                    rest = expand(Product(rest))
                else:
                    rest = 1

                result = self.collector(pymbolic.flattened_sum(
                       pymbolic.flattened_product(leading) * expand(sumchild*rest)
                       for sumchild in sum.children
                       ))
                return result

        return expand(IdentityMapper.map_product(self, expr))

    def map_quotient(self, expr):
        raise NotImplementedError

    def map_power(self, expr):
        from pymbolic.primitives import Expression, Sum

        if isinstance(expr.base, Product):
            return self.rec(pymbolic.flattened_product(
                child**expr.exponent for child in newbase))

        if isinstance(expr.exponent, int):
            newbase = self.rec(expr.base)
            if isinstance(newbase, Sum):
                return self.map_product(pymbolic.flattened_product(expr.exponent*(newbase,)))
            else:
                return IdentityMapper.map_power(self, expr)
        else:
            return IdentityMapper.map_power(self, expr)




def expand(expr, parameters=set(), commutative=True):
    if commutative:
        return ExpandMapper(TermCollector(parameters))(expr)
    else:
        return ExpandMapper(lambda x: x)(expr)
