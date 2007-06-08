import traits
import pymbolic.mapper.stringifier




class Expression(object):
    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        if other:
            return Sum((self, other))
        else:
            return self

    def __radd__(self, other):
        assert not isinstance(other, Expression)
        return Sum((other, self))

    def __sub__(self, other):
        if other:
            return Sum((self, -other))
        else:
            return self

    def __rsub__(self, other):
        assert not isinstance(other, Expression)
        if other:
            return Sum((other, -self))
        else:
            return -self

    def __mul__(self, other):
        if not (other - 1):
            return self
        elif not (other+1):
            return Negation(self)
        elif not other:
            return 0
        return Product((self, other))

    def __rmul__(self, other):
        assert not isinstance(other, Expression)

        if not (other-1):
            return self
        elif not other:
            return 0
        elif not (other+1):
            return -self
        else:
            return Product((other, self))

    def __div__(self, other):
        if not (other-1):
            return self
        return quotient(self, other)
    __truediv__ = __div__

    def __rdiv__(self, other):
        assert not isinstance(other, Expression)
        return quotient(other, self)

    def __pow__(self, other):
        if not other: # exponent zero
            return 1
        elif not (other-1): # exponent one
            return self
        return Power(self, other)

    def __rpow__(self, other):
        assert not isinstance(other, Expression)
        if not other: # base zero
            return 0
        elif not (other-1): # base one
            return 1
        return Power(other, self)

    def __neg__(self):
        return Negation(self)

    def __call__(self, *pars):
        return Call(self, pars)

    def __getitem__(self, subscript):
        return Subscript(self, subscript)

    
    def __hash__(self):
        try:
            return self._HashValue
        except AttributeError:
            from pymbolic.mapper.hash_generator import HashMapper
            self._HashValue = self.invoke_mapper(HashMapper())
            return self._HashValue

    def __float__(self):
        from pymbolic.mapper.evaluator import evaluate_to_float
        return evaluate_to_float(self)

    def __str__(self):
        from pymbolic.mapper.stringifier import StringifyMapper, PREC_NONE
        return StringifyMapper()(self, PREC_NONE)

    def __repr__(self):
        initargs_str = ", ".join(repr(i) for i in self.__getinitargs__())

        return "%s(%s)" % (self.__class__.__name__, initargs_str)

class AlgebraicLeaf(Expression):
    pass

class Leaf(AlgebraicLeaf):
    pass

class Variable(Leaf):
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

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_variable(self, *args, **kwargs)

class Call(AlgebraicLeaf):
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

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_call(self, *args, **kwargs)

class Subscript(AlgebraicLeaf):
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

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_subscript(self, *args, **kwargs)
        


class ElementLookup(AlgebraicLeaf):
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
        return isinstance(other, ElementLookup) \
               and (self._Aggregate == other._Aggregate) \
               and (self._Name == other._Name)

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_lookup(self, *args, **kwargs)

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

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_negation(self, *args, **kwargs)

class Sum(Expression):
    def __init__(self, children):
        assert isinstance(children, tuple)

        self._Children = children

    def __getinitargs__(self):
        return self._Children

    def _children(self):
        return self._Children
    children = property(_children)

    def __eq__(self, other):
        return isinstance(other, Sum) and (self._Children == other._Children)

    def __add__(self, other):
        if isinstance(other, Sum):
            return Sum(self._Children + other._Children)
        if not other:
            return self
        return Sum(self._Children + (other,))

    def __radd__(self, other):
        if isinstance(other, Sum):
            return Sum(other._Children + self._Children)
        if not other:
            return self
        return Sum((other,) + self._Children)

    def __sub__(self, other):
        if not other:
            return self
        return Sum(self._Children + (-other,))

    def __nonzero__(self):
        if len(self._Children) == 0:
            return True
        elif len(self._Children) == 1:
            return bool(self._Children[0])
        else:
            # FIXME: Right semantics?
            return True

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_sum(self, *args, **kwargs)

class Product(Expression):
    def __init__(self, children):
        assert isinstance(children, tuple)
        self._Children = children

    def __getinitargs__(self):
        return self._Children

    def _children(self):
        return self._Children
    children = property(_children)

    def __eq__(self, other):
        return isinstance(other, Product) and (self._Children == other._Children)

    def __mul__(self, other):
        if isinstance(other, Product):
            return Product(self._Children + other._Children)
        if not other:
            return 0
        if not other-1:
            return self
        return Product(self._Children + (other,))

    def __rmul__(self, other):
        if isinstance(other, Product):
            return Product(other._Children + self._Children)
        if not other:
            return 0
        if not other-1:
            return self
        return Product((other,) + self._Children)

    def __nonzero__(self):
        for i in self._Children:
            if not i:
                return False
        return True

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_product(self, *args, **kwargs)

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
        from pymbolic.rational import Rational
        return isinstance(other, (Rational, Quotient)) \
               and (self._Numerator == other.numerator) \
               and (self._Denominator == other.denominator)

    def __nonzero__(self):
        return bool(self._Numerator)

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_quotient(self, *args, **kwargs)

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

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_power(self, *args, **kwargs)

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

    def invoke_mapper(self, mapper, *args, **kwargs):
        return mapper.map_list(self, *args, **kwargs)





# intelligent makers ---------------------------------------------------------
def make_variable(var_or_string):
    if not isinstance(var_or_string, Variable):
        return Variable(var_or_string)
    else:
        return var_or_string




def subscript(expression, index):
    return Subscript(expression, index)




def sum(components):
    it = components.__iter__()
    try:
        result = it.next()
    except StopIteration:
        return 0

    for i in it:
        result = result + i
    return result




def linear_combination(coefficients, expressions):
    return sum(coefficient * expression
                 for coefficient, expression in zip(coefficients, expressions)
                 if coefficient and expression)




def product(components):
    components = tuple(c for c in components if (c-1))

    # flatten any potential sub-products
    queue = list(components)
    done = []

    while queue:
        item = queue.pop(0)
        if isinstance(item, Product):
            queue += item.children
        else:
            done.append(item)

    if len(done) == 0:
        return 1
    elif len(done) == 1:
        return components[0]
    else:
        return Product(tuple(done))




def polynomial_from_expression(expression):
    pass




def quotient(numerator, denominator):
    if not (denominator-1):
        return numerator

    import pymbolic.rational as rat
    if isinstance(numerator, rat.Rational) and \
            isinstance(denominator, rat.Rational):
        return numerator * denominator.reciprocal()

    try:
        c_traits = traits.common_traits(numerator, denominator)
        if isinstance(c_traits, traits.EuclideanRingTraits):
            return rat.Rational(numerator, denominator)
    except traits.NoCommonTraitsError:
        pass
    except traits.NoTraitsError:
        pass

    return Quotient(numerator, denominator)

