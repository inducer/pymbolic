import traits
import pymbolic.mapper.stringifier




class Expression(object):
    def __ne__(self, other):
        return not self.__eq__(other)

    def __add__(self, other):
        if not is_valid_operand(other):
            return NotImplemented
        if is_nonzero(other):
            if self:
                if isinstance(other, Sum):
                    return Sum((self,) + other.children)
                else:
                    return Sum((self, other))
            else:
                return other
        else:
            return self

    def __radd__(self, other):
        assert is_constant(other)
        if is_nonzero(other):
            if self:
                return Sum((other, self))
            else:
                return other
        else:
            return self

    def __sub__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if is_nonzero(other):
            return self.__add__(-other)
        else:
            return self

    def __rsub__(self, other):
        if not is_constant(other):
            return NotImplemented

        if is_nonzero(other):
            return Sum((other, -self))
        else:
            return -self

    def __mul__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if is_zero(other - 1):
            return self
        elif is_zero(other):
            return 0
        else:
            return Product((self, other))

    def __rmul__(self, other):
        if not is_constant(other):
            return NotImplemented

        if is_zero(other-1):
            return self
        elif is_zero(other):
            return 0
        else:
            return Product((other, self))

    def __div__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if is_zero(other-1):
            return self
        return quotient(self, other)
    __truediv__ = __div__

    def __rdiv__(self, other):
        if not is_constant(other):
            return NotImplemented

        return quotient(other, self)

    def __pow__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if is_zero(other): # exponent zero
            return 1
        elif is_zero(other-1): # exponent one
            return self
        return Power(self, other)

    def __rpow__(self, other):
        assert is_constant(other)

        if is_zero(other): # base zero
            return 0
        elif is_zero(other-1): # base one
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

    def stringifier(self):
        from pymbolic.mapper.stringifier import StringifyMapper
        return StringifyMapper

    def __str__(self):
        from pymbolic.mapper.stringifier import PREC_NONE
        return self.stringifier()()(self, PREC_NONE)

    def __repr__(self):
        initargs_str = ", ".join(repr(i) for i in self.__getinitargs__())

        return "%s(%s)" % (self.__class__.__name__, initargs_str)





class AlgebraicLeaf(Expression):
    pass




class Leaf(AlgebraicLeaf):
    pass




class Constant(Leaf):
    def __init__(self, value):
        self.value = value

    def __getinitargs__(self):
        return self.value,

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.value)

    def get_mapper_method(self, mapper):
        return mapper.map_constant




class Variable(Leaf):
    def __init__(self, name):
        self.name = name

    def __getinitargs__(self):
        return self.name,

    def __lt__(self, other):
        if isinstance(other, Variable):
            return self.name.__lt__(other.name)
        else:
            return NotImplemented

    def __eq__(self, other):
        return (isinstance(other, Variable) 
                and self.name == other.name)

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.name)

    def get_mapper_method(self, mapper):
        return mapper.map_variable

class Call(AlgebraicLeaf):
    def __init__(self, function, parameters):
        self.function = function
        self.parameters = parameters

    def __getinitargs__(self):
        return self.function, self.parameters

    def __eq__(self, other):
        return isinstance(other, Call) \
               and (self.function == other.function) \
               and (self.parameters == other.parameters)

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.function, self.parameters)

    def get_mapper_method(self, mapper):
        return mapper.map_call




class Subscript(AlgebraicLeaf):
    def __init__(self, aggregate, index):
        self.aggregate = aggregate
        self.index = index

    def __getinitargs__(self):
        return self.aggregate, self.index

    def __eq__(self, other):
        return isinstance(other, Subscript) \
               and (self.aggregate == other.aggregate) \
               and (self.index == other.index)

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.aggregate, self.index)

    def get_mapper_method(self, mapper):
        return mapper.map_subscript
        



class Lookup(AlgebraicLeaf):
    def __init__(self, aggregate, name):
        self.aggregate = aggregate
        self.name = name

    def __getinitargs__(self):
        return self.aggregate, self.name

    def __eq__(self, other):
        return isinstance(other, Lookup) \
               and (self.aggregate == other.aggregate) \
               and (self.name == other.name)

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.aggregate, self.name)

    def get_mapper_method(self, mapper):
        return mapper.map_lookup




class Sum(Expression):
    def __init__(self, children):
        assert isinstance(children, tuple)

        self.children = children

    def __getinitargs__(self):
        return self.children

    def __eq__(self, other):
        return (isinstance(other, Sum) 
                and (set(self.children) == set(other.children)))

    def __add__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if isinstance(other, Sum):
            return Sum(self.children + other.children)
        if not other:
            return self
        return Sum(self.children + (other,))

    def __radd__(self, other):
        if not is_constant(other):
            return NotImplemented

        if isinstance(other, Sum):
            return Sum(other.children + self.children)
        if not other:
            return self
        return Sum((other,) + self.children)

    def __sub__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if not other:
            return self
        return Sum(self.children + (-other,))

    def __nonzero__(self):
        if len(self.children) == 0:
            return True
        elif len(self.children) == 1:
            return bool(self.children[0])
        else:
            # FIXME: Right semantics?
            return True

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.children)

    def get_mapper_method(self, mapper):
        return mapper.map_sum




class Product(Expression):
    def __init__(self, children):
        assert isinstance(children, tuple)
        self.children = children

    def __getinitargs__(self):
        return self.children

    def __eq__(self, other):
        return (isinstance(other, Product) 
                and (set(self.children) == set(other.children)))

    def __mul__(self, other):
        if not is_valid_operand(other):
            return NotImplemented
        if isinstance(other, Product):
            return Product(self.children + other.children)
        if is_zero(other):
            return 0
        if is_zero(other-1):
            return self
        return Product(self.children + (other,))

    def __rmul__(self, other):
        if not is_constant(other):
            return NotImplemented
        if isinstance(other, Product):
            return Product(other.children + self.children)
        if is_zero(other):
            return 0
        if is_zero(other-1):
            return self
        return Product((other,) + self.children)

    def __nonzero__(self):
        for i in self.children:
            if is_zero(i):
                return False
        return True

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.children)

    def get_mapper_method(self, mapper):
        return mapper.map_product




class Quotient(Expression):
    def __init__(self, numerator, denominator=1):
        self.numerator = numerator
        self.denominator = denominator

    def __getinitargs__(self):
        return self.numerator, self.denominator

    @property
    def num(self):
        return self.numerator

    @property
    def den(self):
        return self.denominator

    def __eq__(self, other):
        from pymbolic.rational import Rational
        return isinstance(other, (Rational, Quotient)) \
               and (self.numerator == other.numerator) \
               and (self.denominator == other.denominator)

    def __nonzero__(self):
        return bool(self.numerator)

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.numerator, self.denominator)

    def get_mapper_method(self, mapper):
        return mapper.map_quotient




class Power(Expression):
    def __init__(self, base, exponent):
        self.base = base
        self.exponent = exponent

    def __getinitargs__(self):
        return self.base, self.exponent

    def __eq__(self, other):
        return isinstance(other, Power) \
               and (self.base == other.base) \
               and (self.exponent == other.exponent)

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.base, self.exponent)

    def get_mapper_method(self, mapper):
        return mapper.map_power




class Vector(Expression):
    """An immutable sequence that you can compute with."""

    def __init__(self, children):
        assert isinstance(children, tuple)
        self.children = children

    def __nonzero__(self):
        for i in self.children:
            if is_nonzero(i):
                return False
        return True

    def __len__(self):
        return len(self.children)

    def __getitem__(self, index):
        if is_constant(index):
            return self.children[index]
        else:
            return Expression.__getitem__(self, index)

    def __neg__(self):
        return Vector(tuple(-x for x in self))

    def __add__(self, other):
        if len(other) != len(self):
            raise ValueError, "can't add values of differing lengths"
        return Vector(tuple(x+y for x, y in zip(self, other)))

    def __radd__(self, other):
        if len(other) != len(self):
            raise ValueError, "can't add values of differing lengths"
        return Vector(tuple(y+x for x, y in zip(self, other)))

    def __sub__(self, other):
        if len(other) != len(self):
            raise ValueError, "can't subtract values of differing lengths"
        return Vector(tuple(x-y for x, y in zip(self, other)))

    def __rsub__(self, other):
        if len(other) != len(self):
            raise ValueError, "can't subtract values of differing lengths"
        return Vector(tuple(y-x for x, y in zip(self, other)))

    def __mul__(self, other):
        return Vector(tuple(x*other for x in self))

    def __rmul__(self, other):
        return Vector(tuple(other*x for x in self))

    def __div__(self, other):
        return Vector(tuple(operator.div(x, other) for x in self))

    def __truediv__(self, other):
        return Vector(tuple(operator.truediv(x, other) for x in self))

    def __floordiv__(self, other):
        return Vector(tuple(x//other for x in self))

    def __getinitargs__(self):
        return self.children

    def __hash__(self):
        from pytools import hash_combine
        return hash_combine(self.__class__, self.children)

    def get_mapper_method(self, mapper):
        return mapper.map_vector




# intelligent makers ---------------------------------------------------------
def make_variable(var_or_string):
    if not isinstance(var_or_string, Expression):
        return Variable(var_or_string)
    else:
        return var_or_string




def subscript(expression, index):
    return Subscript(expression, index)




def flattened_sum(components):
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




def flattened_product(components):
    # flatten any potential sub-products
    queue = list(components)
    done = []

    while queue:
        item = queue.pop(0)

        if is_zero(item-1):
            continue

        if isinstance(item, Product):
            queue += item.children
        else:
            done.append(item)

    if len(done) == 0:
        return 1
    elif len(done) == 1:
        return done[0]
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




# tool functions --------------------------------------------------------------
VALID_CONSTANT_CLASSES = [int, float, complex]
VALID_OPERANDS = [Expression]



def is_constant(value):
    return isinstance(value, tuple(VALID_CONSTANT_CLASSES))

def is_valid_operand(value):
    return isinstance(value, tuple(VALID_OPERANDS)) or is_constant(value)




def register_constant_class(class_):
    VALID_CONSTANT_CLASSES.append(class_)

def unregister_constant_class(class_):
    VALID_CONSTANT_CLASSES.remove(class_)




def is_nonzero(value):
    try:
        return bool(value)
    except ValueError:
        return True

def is_zero(value):
    return not is_nonzero(value)






