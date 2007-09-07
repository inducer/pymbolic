import traits
import pymbolic.mapper.stringifier




VALID_CONSTANT_CLASSES = [int, float, complex]




def is_constant(value):
    return isinstance(value, tuple(VALID_CONSTANT_CLASSES))

def is_valid_operand(value):
    return isinstance(value, Expression) or is_constant(value)




def register_constant_class(class_):
    VALID_CONSTANT_CLASSES.append(class_)

def unregister_constant_class(class_):
    VALID_CONSTANT_CLASSES.remove(class_)




class Expression(object):
    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        if not is_valid_operand(other):
            return NotImplemented
        if other:
            if self:
                return Sum((self, other))
            else:
                return other
        else:
            return self

    def __radd__(self, other):
        assert is_constant(other)
        if other:
            if self:
                return Sum((other, self))
            else:
                return other
        else:
            return self

    def __sub__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if other:
            return Sum((self, -other))
        else:
            return self

    def __rsub__(self, other):
        assert is_constant(other)

        if other:
            return Sum((other, -self))
        else:
            return -self

    def __mul__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if not (other - 1):
            return self
        elif not other:
            return 0
        return Product((self, other))

    def __rmul__(self, other):
        assert is_constant(other)

        if not (other-1):
            return self
        elif not other:
            return 0
        elif not (other+1):
            return -self
        else:
            return Product((other, self))

    def __div__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if not (other-1):
            return self
        return quotient(self, other)
    __truediv__ = __div__

    def __rdiv__(self, other):
        assert is_constant(other)
        return quotient(other, self)

    def __pow__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if not other: # exponent zero
            return 1
        elif not (other-1): # exponent one
            return self
        return Power(self, other)

    def __rpow__(self, other):
        assert is_constant(other)

        if not other: # base zero
            return 0
        elif not (other-1): # base one
            return 1
        return Power(other, self)

    def __neg__(self):
        return -1*self

    def __call__(self, *pars):
        return Call(self, pars)

    def __getitem__(self, subscript):
        return Subscript(self, subscript)
    
    def __float__(self):
        from pymbolic.mapper.evaluator import evaluate_to_float
        return evaluate_to_float(self)

    def stringify(self, enclosing_prec, use_repr_for_constants=False):
        from pymbolic.mapper.stringifier import StringifyMapper
        return StringifyMapper(use_repr_for_constants)(self, enclosing_prec)

    def __str__(self):
        from pymbolic.mapper.stringifier import PREC_NONE
        return self.stringify(PREC_NONE)

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

    def __hash__(self):
        return 0x111 ^ hash(self.name)

    def get_mapper_method(self, mapper):
        return mapper.map_variable

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

    def __hash__(self):
        return hash(self.function) ^ hash(self.parameters)

    def get_mapper_method(self, mapper):
        return mapper.map_call

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

    def __hash__(self):
        return 0x123 ^ hash(self.aggregate) ^ hash(self.index)

    def get_mapper_method(self, mapper):
        return mapper.map_subscript(self)
        


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

    def __hash__(self):
        return 0x183 ^ hash(self.aggregate) ^ hash(self.name)

    def get_mapper_method(self, mapper):
        return mapper.map_lookup

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

    def __hash__(self):
        return 0x456 ^ hash(self.children)

    def get_mapper_method(self, mapper):
        return mapper.map_sum

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

    def __hash__(self):
        return 0x789 ^ hash(self.children)

    def get_mapper_method(self, mapper):
        return mapper.map_product

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

    def __hash__(self):
        return 0xabc ^ hash(self.numerator) ^ hash(self.denominator)

    def get_mapper_method(self, mapper):
        return mapper.map_quotient

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

    def __hash__(self):
        return 0xdef ^ hash(self.base) ^ hash(self.exponent)

    def get_mapper_method(self, mapper):
        return mapper.map_power





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

