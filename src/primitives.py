import traits
import rational as rat
import pymbolic.mapper.stringifier
import pymbolic.mapper.hash_generator




class Expression(object):
    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if not other:
            return self
        return Sum(self, other)

    def __radd__(self, other):
        assert not isinstance(other, Expression)

        if not other:
            return self
        else:
            other = Constant(other)
        return Sum(other, self)

    def __sub__(self, other):
        if not isinstance(other, Expression):
                other = Constant(other)
        if not other:
            return self
        return Sum(self, -other)

    def __rsub__(self, other):
        assert not isinstance(other, Expression)

        if not other:
            return Negation(self)
        else:
            other = Constant(other)
        return Sum(other, -self)

    def __mul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if not (other - 1):
            return self
        elif not (other+1):
            return Negation(self)
        elif not other:
            return Constant(0)
        return Product(self, other)

    def __rmul__(self, other):
        assert not isinstance(other, Expression)

        if not (other-1):
            return self
        elif not other:
            return Constant(0)
        elif not (other+1):
            return Negation(self)
        else:
            return Product(Constant(other), self)

    def __div__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        if not (other-1):
            return self
        return make_quotient(self, other)

    def __rdiv__(self, other):
        assert not isinstance(other, Expression)
        return make_quotient(Constant(other), self)

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

    def __hash__(self):
        try:
            return self._HashValue
        except AttributeError:
            self._HashValue = self.invoke_mapper(pymbolic.mapper.hash_generator.HashMapper())
            return self._HashValue

    def __str__(self):
        return self.invoke_mapper(pymbolic.mapper.stringifier.StringifyMapper())

    def __repr__(self):
        return "%s%s" % (self.__class__.__name__, repr(self.__getinitargs__()))

class Constant(Expression):
    def __init__(self, value):
        self._Value = value

    def __getinitargs__(self):
        return self._Value,

    def _value(self):
        return self._Value
    value = property(_value)

    def __lt__(self, other):
        if isinstance(other, Variable):
            return self._Value.__lt__(other._Value)
        else:
            return NotImplemented

    def __eq__(self, other):
        return isinstance(other, Constant) and self._Value == other._Value

    def __add__(self, other):
        if not isinstance(other, Expression):
            return Constant(self._Value + other)
        if isinstance(other, Constant):
            return Constant(self._Value + other._Value)
        if self._Value == 0:
            return other
        return Expression.__add__(self, other)

    def __radd__(self, other):
        if not isinstance(other, Expression):
            return Constant(other + self._Value)
        if self._Value == 0:
            return other
        return Expression.__radd__(self, other)

    def __sub__(self, other):
        if not isinstance(other, Expression):
            return Constant(self._Value - other)
        if isinstance(other, Constant):
            return Constant(self._Value - other._Value)
        if self._Value == 0:
            return Negation(other)
        return Expression.__sub__(self, other)

    def __rsub__(self, other):
        if not isinstance(other, Expression):
            return Constant(other - self._Value)
        if self._Value == 0:
            return other
        return Expression.__rsub__(self, other)

    def __mul__(self, other):
        if not isinstance(other, Expression):
            return Constant(self._Value * other)
        if isinstance(other, Constant):
            return Constant(self._Value * other._Value)
        if self._Value == 1:
            return other
        if self._Value == 0:
            return self
        return Expression.__mul__(self, other)

    def __rmul__(self, other):
        if not isinstance(other, Expression):
            return Constant(other * self._Value)
        if self._Value == 1:
            return other
        if self._Value == 0:
            return self
        return Expression.__rmul__(self, other)

    def __div__(self, other):
        if not isinstance(other, Expression):
            return Constant(self._Value / other)
        if isinstance(other, Constant):
            return Constant(self._Value / other._Value)
        if self._Value == 0:
            return self
        return Expression.__div__(self, other)

    def __rdiv__(self, other):
        if not isinstance(other, Expression):
            return Constant(other / self._Value)
        if self._Value == 1:
            return other
        return Expression.__rdiv__(self, other)

    def __pow__(self, other):
        if not isinstance(other, Expression):
            return Constant(self._Value ** other)
        if isinstance(other, Constant):
            return Constant(self._Value ** other._Value)
        if self._Value == 1:
            return self
        return Expression.__pow__(self, other)

    def __rpow__(self, other):
        if not isinstance(other, Expression):
            return Constant(other ** self._Value)
        if self._Value == 0:
            return Constant(1)
        if self._Value == 1:
            return other
        return Expression.__rpow__(self, other)

    def __neg__(self):
        return Constant(-self._Value)

    def __call__(self, *pars):
        for par in pars:
            if isinstance(par, Expression):
                return Expression.__call__(self, *pars)
        return self._Value(*pars)

    def __nonzero__(self):
        return bool(self._Value)

    def invoke_mapper(self, mapper):
        return mapper.map_constant(self)


class Variable(Expression):
    def __init__(self, name):
        self._Name = name

    def __getinitargs__(self):
        return self._Name,

    def _name(self):
        return self._Name
    name = property(_name)

    def __lt__(self, other):
        if isinstance(other, Variable):
            return self._Name.__lt__(other._Name)
        else:
            return NotImplemented

    def __eq__(self, other):
        return isinstance(other, Variable) and self._Name == other._Name

    def invoke_mapper(self, mapper):
        return mapper.map_variable(self)

class Call(Expression):
    def __init__(self, function, parameters):
        self._Function = function
        self._Parameters = parameters

    def __getinitargs__(self):
        return self._Function, self._Parameters

    def _function(self):
        return self._Function
    function = property(_function)

    def _parameters(self):
        return self._Parameters
    parameters = property(_parameters)

    def __eq__(self, other):
        return isinstance(other, Call) \
               and (self._Function == other._Function) \
               and (self._Parameters == other._Parameters)

    def invoke_mapper(self, mapper):
        return mapper.map_call(self)

class Subscript(Expression):
    def __init__(self, aggregate, index):
        self._Aggregate = aggregate
        self._Index = index

    def __getinitargs__(self):
        return self._Aggregate, self._Index

    def _aggregate(self):
        return self._Aggregate
    aggregate = property(_aggregate)

    def _index(self):
        return self._Index
    index = property(_index)

    def __eq__(self, other):
        return isinstance(other, Subscript) \
               and (self._Aggregate == other._Aggregate) \
               and (self._Index == other._Index)

    def invoke_mapper(self, mapper):
        return mapper.map_subscript(self)

class ElementLookup(Expression):
    def __init__(self, aggregate, name):
        self._Aggregate = aggregate
        self._Name = name

    def __getinitargs__(self):
        return self._Aggregate, self._Name

    def _aggregate(self):
        return self._Aggregate
    aggregate = property(_aggregate)

    def _name(self):
        return self._Name
    name = property(_name)

    def __eq__(self, other):
        return isinstance(other, Subscript) \
               and (self._Aggregate == other._Aggregate) \
               and (self._Name == other._Name)

    def invoke_mapper(self, mapper):
        return mapper.map_lookup(self)

class Negation(Expression):
    def __init__(self, child):
        self._Child = child

    def __getinitargs__(self):
        return self._Child, 

    def _child(self):
        return self._Child
    child = property(_child)

    def __eq__(self, other):
        return isinstance(other, Negation) and (self.Child == other.Child)

    def invoke_mapper(self, mapper):
        return mapper.map_negation(self)

class Sum(Expression):
    def __init__(self, *children):
        self._Children = children

    def __getinitargs__(self):
        return self._Children

    def _children(self):
        return self._Children
    children = property(_children)

    def __eq__(self, other):
        return isinstance(other, Sum) and (self._Children == other._Children)

    def __add__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        elif isinstance(other, Sum):
            return Sum(*(self._Children + other._Children))
        return Sum(*(self._Children + (other,)))

    def __radd__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        elif isinstance(other, Sum):
            return Sum(*(other._Children + self._Children))
        return Sum(*((other,) + self._Children))

    def __sub__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        return Sum(*(self._Children + (-other,)))

    def __nonzero__(self):
        if len(self._Children) == 0:
            return True
        elif len(self._Children) == 1:
            return bool(self._Children[0])
        else:
            # FIXME: Right semantics?
            return True

    def invoke_mapper(self, mapper):
        return mapper.map_sum(self)

class Product(Expression):
    def __init__(self, *children):
        self._Children = children

    def __getinitargs__(self):
        return self._Children

    def _children(self):
        return self._Children
    children = property(_children)

    def __eq__(self, other):
        return isinstance(other, Product) and (self._Children == other._Children)

    def __mul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        elif isinstance(other, Product):
            return Product(*(self._Children + other._Children))
        return Product(*(self._Children + (other,)))

    def __rmul__(self, other):
        if not isinstance(other, Expression):
            other = Constant(other)
        elif isinstance(other, Product):
            return Product(*(other._Children + self._Children))
        return Product(*((other,) + self._Children))

    def __nonzero__(self):
        for i in self._Children:
            if not i:
                return False
        return True

    def invoke_mapper(self, mapper):
        return mapper.map_product(self)

class Quotient(Expression):
    def __init__(self, numerator, denominator=1):
        self._Numerator = numerator
        self._Denominator = denominator

    def __getinitargs__(self):
        return self._Numerator, self._Denominator

    def _num(self):
        return self._Numerator
    numerator=property(_num)

    def _den(self):
        return self._Denominator
    denominator=property(_den)

    def __eq__(self, other):
        return isinstance(other, Subscript) \
               and (self._Numerator == other._Numerator) \
               and (self._Denominator == other._Denominator)

    def __nonzero__(self):
        return bool(self._Numerator)

    def invoke_mapper(self, mapper):
        return mapper.map_rational(self)

class RationalExpression(Expression):
    def __init__(self, rational):
        self.Rational = rational

    def _num(self):
        return self.Rational.numerator
    numerator=property(_num)

    def _den(self):
        return self.Rational.denominator
    denominator=property(_den)

    def __nonzero__(self):
        return bool(self.Rational)

    def invoke_mapper(self, mapper):
        return mapper.map_rational(self)

class Power(Expression):
    def __init__(self, base, exponent):
        self._Base = base
        self._Exponent = exponent

    def __getinitargs__(self):
        return self._Base, self._Exponent

    def _base(self):
        return self._Base
    base = property(_base)

    def _exponent(self):
        return self._Exponent
    exponent = property(_exponent)

    def __eq__(self, other):
        return isinstance(other, Power) \
               and (self._Base == other._Base) \
               and (self._Exponent == other._Exponent)

    def invoke_mapper(self, mapper):
        return mapper.map_power(self)

class PolynomialExpression(Expression):
    def __init__(self, base=None, data=None, polynomial=None):
        if polynomial:
            self._Polynomial = polynomial
        else:
            self._Polynomial = polynomial.Polynomial(base, data)
            
    def _polynomial(self):
        return self._Polynomial
    polynomial = property(_polynomial)

    def __eq__(self, other):
        return isinstance(other, PolynomialExpression) \
               and (self._Polynomial == other._Polynomial)

    def invoke_mapper(self, mapper):
        return mapper.map_polynomial(self)

class List(Expression):
    def __init__(self, children):
        assert isinstance(children, tuple)
        self._Children = children

    def _children(self):
        return self.Children
    children = property(_children)

    def __eq__(self, other):
        return isinstance(other, List) \
               and (self.Children == other.Children)

    def invoke_mapper(self, mapper):
        return mapper.map_list(self)





# intelligent makers ---------------------------------------------------------
def subscript(expression, index):
    if not isinstance(index, Expression):
        index = Constant(index)
    return Subscript(expression, index)




def sum(*components):
    components = tuple(c for c in components if c)
    if len(components) == 0:
        return Constant(0)
    elif len(components) == 1:
        return components[0]
    else:
        return Sum(*components)




def linear_combination(coefficients, expressions):
    return sum(*[coefficient * expression
                 for coefficient, expression in zip(coefficients, expressions)
                 if coefficient and expression])




def product(*components):
    for c in components:
        if not c:
            return Constant(0)

    components = tuple(c for c in components if (c-1))

    if len(components) == 0:
        return Constant(1)
    elif len(components) == 1:
        return components[0]
    else:
        return Product(*components)




def polynomial_from_expression(expression):
    pass




def make_quotient(numerator, denominator):
    try:
        if isinstance(traits.common_traits(numerator, denominator), 
                      EuclideanRingTraits):
            return RationalExpression(numerator, denominator)
    except traits.NoCommonTraitsError:
        pass
    except traits.NoTraitsError:
        pass

    return Quotient(numerator, denominator)

