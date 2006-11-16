import pymbolic
from pymbolic.mapper import IdentityMapper
from pymbolic.primitives import Sum, Product




class CommutativeTermCollector(object):
    """A term collector that assumes that multiplication is commutative.
    """

    def __init__(self, term_less, is_parameter):
        self.TermLess = term_less
        self.IsParameter = is_parameter

    def normal_form(self, product):
        assert isinstance(product, Product)

        def extract_base(term):
            if isinstance(term, Power):
                pass


    def __call__(self, mysum):
        assert isinstance(mysum, Sum)
        termhash = {}
        for child in mysum.children:
            pass


class ExpandMapper(IdentityMapper):
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
                return pymbolic.product(children)
            else:
                sum = children[len(leading)]
                assert isinstance(sum, Sum)
                rest = children[len(leading)+1:]

                return pymbolic.sum(
                       expand(leading+[sumchild]+rest)
                       for sumchild in sum.children)

        return expand([self.rec(child) for child in expr.children])

    def map_quotient(self, expr):
        raise NotImplementedError

    def map_power(self, expr):
        from pymbolic.primitives import Expression, Sum

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
