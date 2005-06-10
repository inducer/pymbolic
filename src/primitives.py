import tests
import stringifier




class Expression:
    def __add__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if tests.is_zero(other):
            return self
        return Sum((self, other))

    def __radd__(self, other):
        assert not isinstance(other, Expression)

        if other == 0:
            return self
        else:
            other = Constant(other)
        return Sum((other, self))

    def __sub__(self, other):
        if not isinstance(other, Expression):
                other = Constant(other)
        if tests.is_zero(other):
            return self
        return Sum((self, -other))

    def __rsub__(self, other):
        assert not isinstance(other, Expression)

        if other == 0:
            return Negation(self)
        else:
            other = Constant(other)
        return Sum((other, -self))

    def __mul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if test.is_one(other):
            return self
        if tests.is_zero(other):
            return Constant(0)
        return Product((self, other))

    def __rmul__(self, other):
        assert not isinstance(other, Expression)

        if other == 1:
            return self
        elif other == 0:
            return Constant(0)
        else:
            return Product((other, self))

    def __div__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if isinstance(other, Constant) and other.Value == 1:
            return self
        return Quotient(self, other)

    def __rdiv__(self, other):
        assert not isinstance(other, Expression)
        return Quotient(Constant(other), self)

    def __pow__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if tests.is_zero(other): # exponent zero
            return Constant(1)
        elif tests.is_one(other): # exponent one
            return self
        return Power(self, other)

    def __rpow__(self, other):
        assert not isinstance(other, Expression)
        if tests.is_zero(other): # base zero
            return Constant(0)
        elif tests.is_one(other): # base one
            return Constant(1)
        return Power(other, self)

    def __neg__(self):
        return Negation(self)

    def __call__(self, other):
        processed = []
        for par in other:
            if isinstance(par, Expression):
                processed.append(par)
            else:
                processed.append(Constant(par))

        return Call(self, processed)

    def __str__(self):
        return self.invoke_mapper(stringifier.StringifyMapper())

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

    def invoke_mapper(self, mapper):
        return mapper.map_product(self)

class Quotient(BinaryExpression):
    def invoke_mapper(self, mapper):
        return mapper.map_quotient(self)

class Power(BinaryExpression):
    def invoke_mapper(self, mapper):
        return mapper.map_power(self)

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

