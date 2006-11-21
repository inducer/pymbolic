import pymbolic
from pymbolic.mapper import RecursiveMapper



class CoefficientFinder(RecursiveMapper):
    """Find the coefficient of `term' in `expr'.
    
    The expression to which this is applied should be fully expanded
    and collected. See expander.py.
    """

    def __init__(self, term):
        self.Term = term

    def map_constant(self,expr):
        return 0

    def map_leaf(self, expr):
        if expr == self.Term:
            return 1
        else:
            return 0

    map_call = map_leaf
    map_subscript = map_leaf
    map_lookup = map_leaf
    map_variable = map_leaf
    map_power = map_leaf

    def map_negation(self, expr):
        return -self.rec(expr.child)

    def map_sum(self, expr):
        return pymbolic.sum(self(child) for child in expr.children)

    def map_product(self, expr):
        if expr == self.Term:
            return 1

        # FIXME this is dumber than necessary
        child_coeffs = [self(child) for child in expr.children]
        result = pymbolic.sum(
                pymbolic.product(expr.children[:i])
                *mapped_child*
                pymbolic.product(expr.children[(i+1):])
                for i, mapped_child in enumerate(child_coeffs)
                if mapped_child)
        return result

    def map_quotient(self, expr):
        if expr == self.Term:
            return 1

        if self.Term == pymbolic.quotient(1, expr.denominator):
            return expr.numerator

        return pymbolic.quotient(self(expr.numerator), expr.denominator)

    def map_polynomial(self, expr):
        if expr == self.Term:
            return 1

        # FIXME this is incorrect in a good bunch of cases
        from pymbolic.primitives import Power

        if expr.Base == self.Term:
            return expr.get_coefficient(1)
        elif isinstance(self.Term, Power) and self.Term.base == expr.base and \
        isinstance(expr.exponent, int):
            return expr.get_coefficient(expr.exponent)
        else:
            return pymbolic.sum(self(coeff)*expr.base**exp
                    for exp, coeff in expr.data)





def find_coefficient(expr, term):
    """Find the coefficient of `term' in `expr'.
    
    The expression to which this is applied should be fully expanded
    and collected. See expander.py.
    """

    return CoefficientFinder(term)(expr)
