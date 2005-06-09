import stringifier




class Expression:
    def __add__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Sum((self, other))

    def __radd__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Sum((other, self))

    def __sub__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Sum((self, -other))

    def __rsub__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Sum((other, -self))

    def __mul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Product((self, other))

    def __rmul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Product((other, self))

    def __div__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Quotient(self, other)

    def __rdiv__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Quotient(other, self)

    def __pow__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Power(self, other)

    def __rpow__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Power(other, self)

    def __neg__(self, other):
        return Negation(self, other)

    def __call__(self, other):
        return Call(self, other)

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
        self.Children = children

    def __hash__(self):
        return hash(self.Children)

class Constant(Expression):
    def __init__(self, value):
        self.Value = value

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
    def __init__(self, base, children):
        self.Base = base
        self.Children = children

    def __hash__(self):
        return hash(self.Base) ^ hash(self.Children)

    def invoke_mapper(self, mapper):
        return mapper.map_polynomial(self)

class List(NAryExpression):
    def invoke_mapper(self, mapper):
        return mapper.map_list(self)
