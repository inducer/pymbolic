import mapper.stringifier




class Expression(object):
    def __add__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if not other:
            return self
        return Sum((self, other))

    def __radd__(self, other):
        assert not isinstance(other, Expression)

        if not other:
            return self
        else:
            other = Constant(other)
        return Sum((other, self))

    def __sub__(self, other):
        if not isinstance(other, Expression):
                other = Constant(other)
        if not other:
            return self
        return Sum((self, -other))

    def __rsub__(self, other):
        assert not isinstance(other, Expression)

        if not other:
            return Negation(self)
        else:
            other = Constant(other)
        return Sum((other, -self))

    def __mul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if not (other - 1):
            return self
        if not other:
            return Constant(0)
        return Product((self, other))

    def __rmul__(self, other):
        assert not isinstance(other, Expression)

        if not (other-1):
            return self
        elif not other:
            return Constant(0)
        else:
            return Product((other, self))

    def __div__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if not (other-1):
            return self
        return RationalExpression(self, other)

    def __rdiv__(self, other):
        assert not isinstance(other, Expression)
        return RationalExpression(Constant(other), self)

    def __pow__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if not other: # exponent zero
            return Constant(1)
        elif not (other-1): # exponent one
            return self
        return Power(self, other)

    def __rpow__(self, other):
        assert not isinstance(other, Expression)
        if not other: # base zero
            return Constant(0)
        elif not (other-1): # base one
            return Constant(1)
        return Power(other, self)

    def __neg__(self):
        return Negation(self)

    def __call__(self, *pars):
        processed = []
        for par in pars:
            if isinstance(par, Expression):
                processed.append(par)
            else:
                processed.append(Constant(par))

        return Call(self, tuple(processed))

    def __str__(self):
        return self.invoke_mapper(mapper.stringifier.StringifyMapper())

class UnaryExpression(Expression):
    def __init__(self, child):
        self.Child = child

    def __hash__(self):
        return ~hash(self.Child)

class BinaryExpression(Expression):
    def __init__(self, child1, child2):
        self.Child1 = child1
        self.Child2 = child2

    def __hash__(self):
        return hash(self.Child1) ^ hash(self.Child2)

class NAryExpression(Expression):
    def __init__(self, children):
        assert isinstance(children, tuple)
        self.Children = children

    def __hash__(self):
        return hash(self.Children)

class Constant(Expression):
    def __init__(self, value):
        self.Value = value

    def __eq__(self, other):
        return isinstance(other, Constant) and self.Value == other.Value

    def __ne__(self, other):
        return not isinstance(other, Constant) or self.Value != other.Value

    def __add__(self, other):
        if not isinstance(other, Expression):
            return Constant(self.Value + other)
        if isinstance(other, Constant):
            return Constant(self.Value + other.Value)
        if self.Value == 0:
            return other
        return Expression.__add__(self, other)

    def __radd__(self, other):
        if not isinstance(other, Expression):
            return Constant(other + self.Value)
        if self.Value == 0:
            return other
        return Expression.__radd__(self, other)

    def __sub__(self, other):
        if not isinstance(other, Expression):
            return Constant(self.Value - other)
        if isinstance(other, Constant):
            return Constant(self.Value - other.Value)
        if self.Value == 0:
            return Negation(other)
        return Expression.__sub__(self, other)

    def __rsub__(self, other):
        if not isinstance(other, Expression):
            return Constant(other - self.Value)
        if self.Value == 0:
            return other
        return Expression.__rsub__(self, other)

    def __mul__(self, other):
        if not isinstance(other, Expression):
            return Constant(self.Value * other)
        if isinstance(other, Constant):
            return Constant(self.Value * other.Value)
        if self.Value == 1:
            return other
        if self.Value == 0:
            return self
        return Expression.__mul__(self, other)

    def __rmul__(self, other):
        if not isinstance(other, Expression):
            return Constant(other * self.Value)
        if self.Value == 1:
            return other
        if self.Value == 0:
            return self
        return Expression.__rmul__(self, other)

    def __div__(self, other):
        if not isinstance(other, Expression):
            return Constant(self.Value / other)
        if isinstance(other, Constant):
            return Constant(self.Value / other.Value)
        if self.Value == 0:
            return self
        return Expression.__div__(self, other)

    def __rdiv__(self, other):
        if not isinstance(other, Expression):
            return Constant(other / self.Value)
        if self.Value == 1:
            return other
        return Expression.__rdiv__(self, other)

    def __pow__(self, other):
        if not isinstance(other, Expression):
            return Constant(self.Value ** other)
        if isinstance(other, Constant):
            return Constant(self.Value ** other.Value)
        if self.Value == 1:
            return self
        return Expression.__pow__(self, other)

    def __rpow__(self, other):
        if not isinstance(other, Expression):
            return Constant(other ** self.Value)
        if self.Value == 0:
            return Constant(1)
        if self.Value == 1:
            return other
        return Expression.__rpow__(self, other)

    def __neg__(self):
        return Constant(-self.Value)

    def __call__(self, *pars):
        for par in pars:
            if isinstance(par, Expression):
                return Expression.__call__(self, *pars)
        return self.Value(*pars)

    def __nonzero__(self):
        return bool(self.Value)

    def __hash__(self):
        return hash(self.Value)

    def invoke_mapper(self, mapper):
        return mapper.map_constant(self)


class Variable(Expression):
    def __init__(self, name):
        self.Name = name

    def __hash__(self):
        return hash(self.Name)

    def invoke_mapper(self, mapper):
        return mapper.map_variable(self)

class Call(Expression):
    def __init__(self, func, parameters):
        self.Function = func
        self.Parameters = parameters

    def invoke_mapper(self, mapper):
        return mapper.map_call(self)

    def __hash__(self):
        return hash(self.Function) ^ hash(self.Parameters)

class Sum(NAryExpression):
    def __add__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        elif isinstance(other, Sum):
            return Sum(self.Children + other.Children)
        return Sum(self.Children + (other,))

    def __radd__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        elif isinstance(other, Sum):
            return Sum(other.Children + self.Children)
        return Sum(other, + self.Children)

    def __sub__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Sum(self.Children + (-other,))

    def __nonzero__(self):
        if len(self.Children) == 0:
            return True
        elif len(self.Children) == 1:
            return bool(self.Children[0])
        else:
            # FIXME: Right semantics?
            return False

    def invoke_mapper(self, mapper):
        return mapper.map_sum(self)

class Negation(UnaryExpression):
    def invoke_mapper(self, mapper):
        return mapper.map_negation(self)

class Product(NAryExpression):
    def __mul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        elif isinstance(other, Product):
            return Product(self.Children + other.Children)
        return Product(self.Children + (other,))

    def __rmul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        elif isinstance(other, Product):
            return Product(other.Children + self.Children)
        return Product(other, + self.Children)

    def __nonzero__(self):
        for i in self.Children:
            if not i:
                return False
        return True

    def invoke_mapper(self, mapper):
        return mapper.map_product(self)

class RationalExpression(Expression):
    def __init__(self, numerator=None, denominator=1, rational=None):
        if rational:
            self.Rational = rational
        else:
            self.Rational = rat.Rational(numerator, denominator)

    def _num(self):
        return self.Rational.numerator
    numerator=property(_num)

    def _den(self):
        return self.Rational.denominator
    denominator=property(_den)

    def __nonzero__(self):
        return
        for i in self.Children:
            if not i:
                return False
        return True

    def __hash__(self):
        return hash(self.Rational)

    def invoke_mapper(self, mapper):
        return mapper.map_rational(self)


class Power(BinaryExpression):
    def invoke_mapper(self, mapper):
        return mapper.map_power(self)

class PolynomialExpression(Expression):
    def __init__(self, base=None, data=None, polynomial=None):
        if polynomial:
            self.Polynomial = polynomial
        else:
            self.Polynomial = polynomial.Polynomial(base, data)

    def __hash__(self):
        return hash(self.Polynomial)

    def invoke_mapper(self, mapper):
        return mapper.map_polynomial(self)

class List(NAryExpression):
    def invoke_mapper(self, mapper):
        return mapper.map_list(self)





# intelligent makers ---------------------------------------------------------
def make_sum(components):
    if len(components) == 0:
        return primitives.Constant(0)
    elif len(components) == 1:
        return components[0]
    else:
        return Sum(components)

def make_product(components):
    if len(components) == 0:
        return primitives.Constant(1)
    elif len(components) == 1:
        return components[0]
    else:
        return Product(components)

def polynomial_from_expression(expression):
    pass

