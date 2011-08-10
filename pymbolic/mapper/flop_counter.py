from pymbolic.mapper import CombineMapper




class FlopCounter(CombineMapper):
    def combine(self, values):
        return sum(values)

    def map_constant(self, expr):
        return 0

    def map_variable(self, expr):
        return 0

    def map_sum(self, expr):
        if expr.children:
            return len(expr.children) - 1 + sum(self.rec(ch) for ch in expr.children)
        else:
            return 0

    map_product = map_sum

    def map_quotient(self, expr, *args):
        return 1 + self.rec(expr.numerator) + self.rec(expr.denominator)

    map_floor_div = map_quotient

    def map_power(self, expr, *args):
        return 1 + self.rec(expr.base) + self.rec(expr.exponent)

    def map_if_positive(self, expr):
        return self.rec(expr.criterion) + max(
                self.rec(expr.then),
                self.rec(expr.else_))
