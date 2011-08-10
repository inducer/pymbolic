import traits




class Expression(object):
    """An evaluatable part of a mathematical expression.

    Expression objects are immutable.
    """

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
        if not is_valid_operand(other):
            return NotImplemented

        if is_zero(other):
            return 0
        return quotient(other, self)
    __rtruediv__ = __rdiv__

    def __floordiv__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if is_zero(other-1):
            return self
        return FloorDiv(self, other)

    def __rfloordiv__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if is_zero(self-1):
            return other
        return FloorDiv(other, self)

    def __mod__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if is_zero(other-1):
            return self
        return Remainder(self, other)

    def __rmod__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        return Remainder(other, self)

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
        if subscript == ():
            return self
        else:
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

    # hashable interface ------------------------------------------------------
    def __eq__(self, other):
        """Provides equality testing with quick positive and negative paths
        based on L{id} and L{__hash__}().

        Subclasses should generally not override this method, but instead 
        provide an implementation of L{is_equal}.
        """
        if self is other:
            return True
        elif hash(self) != hash(other):
            return False
        else:
            return self.is_equal(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        """Provides caching for hash values.

        Subclasses should generally not override this method, but instead 
        provide an implementation of L{get_hash}.
        """
        try:
            return self.hash_value
        except AttributeError:
            self.hash_value = self.get_hash()
            return self.hash_value

    # hashable backend --------------------------------------------------------
    def is_equal(self, other):
        raise NotImplementedError("is_equal() in "+str(type(self)))

    def get_hash(self):
        raise NotImplementedError("get_hash() in "+str(type(self)))

    # comparison interface ----------------------------------------------------
    def __le__(self, other): raise TypeError("expressions don't have an order")
    def __lt__(self, other): raise TypeError("expressions don't have an order")
    def __ge__(self, other): raise TypeError("expressions don't have an order")
    def __gt__(self, other): raise TypeError("expressions don't have an order")






class AlgebraicLeaf(Expression):
    """An expression that serves as a leaf for arithmetic evaluation.
    This may end up having child nodes still, but they're not reached by
    ways of arithmetic."""
    pass




class Leaf(AlgebraicLeaf):
    """An expression that is irreducible, i.e. has no Expression-type parts 
    whatsoever."""
    pass




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

    def is_equal(self, other):
        return (other.__class__ == self.__class__
                and self.name == other.name)

    def get_hash(self):
        return hash((self.__class__, self.name))

    mapper_method = intern("map_variable")




class FunctionSymbol(AlgebraicLeaf):
    """Represents the name of a function.

    May optionally have an `arg_count` attribute, which will
    allow `Call` to check the number of arguments.
    """

    def __getinitargs__(self):
        return ()

    def is_equal(self, other):
        return self.__class__ == other.__class

    def get_hash(self):
        return hash(self.__class__)

    mapper_method = intern("map_function_symbol")





class Call(AlgebraicLeaf):
    def __init__(self, function, parameters):
        self.function = function
        self.parameters = parameters

        try:
            arg_count = self.function.arg_count
        except AttributeError:
            pass
        else:
            if len(self.parameters) != arg_count:
                raise TypeError("%s called with wrong number of arguments "
                        "(need %d, got %d)" % (
                            self.function, arg_count, len(parameters)))

    def __getinitargs__(self):
        return self.function, self.parameters

    def is_equal(self, other):
        return isinstance(other, Call) \
               and (self.function == other.function) \
               and (self.parameters == other.parameters)

    def get_hash(self):
        return hash((self.__class__, self.function, self.parameters))

    mapper_method = intern("map_call")




class Subscript(AlgebraicLeaf):
    def __init__(self, aggregate, index):
        self.aggregate = aggregate
        self.index = index

    def __getinitargs__(self):
        return self.aggregate, self.index

    def is_equal(self, other):
        return isinstance(other, Subscript) \
               and (self.aggregate == other.aggregate) \
               and (self.index == other.index)

    def get_hash(self):
        return hash((self.__class__, self.aggregate, self.index))

    mapper_method = intern("map_subscript")




class Lookup(AlgebraicLeaf):
    def __init__(self, aggregate, name):
        self.aggregate = aggregate
        self.name = name

    def __getinitargs__(self):
        return self.aggregate, self.name

    def is_equal(self, other):
        return isinstance(other, Lookup) \
               and (self.aggregate == other.aggregate) \
               and (self.name == other.name)

    def get_hash(self):
        return hash((self.__class__, self.aggregate, self.name))

    mapper_method = intern("map_lookup")




class Sum(Expression):
    def __init__(self, children):
        assert isinstance(children, tuple)

        self.children = children

    def __getinitargs__(self):
        return self.children

    def is_equal(self, other):
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

    def get_hash(self):
        return hash((self.__class__, self.children))

    mapper_method = intern("map_sum")




class Product(Expression):
    def __init__(self, children):
        assert isinstance(children, tuple)
        self.children = children

    def __getinitargs__(self):
        return self.children

    def is_equal(self, other):
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

    def get_hash(self):
        return hash((self.__class__, self.children))

    mapper_method = intern("map_product")




class QuotientBase(Expression):
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

    def __nonzero__(self):
        return bool(self.numerator)

    def get_hash(self):
        return hash((self.__class__, self.numerator, self.denominator))




class Quotient(QuotientBase):
    def is_equal(self, other):
        from pymbolic.rational import Rational
        return isinstance(other, (Rational, Quotient)) \
               and (self.numerator == other.numerator) \
               and (self.denominator == other.denominator)

    mapper_method = intern("map_quotient")




class FloorDiv(QuotientBase):
    mapper_method = intern("map_floor_div")




class Remainder(QuotientBase):
    def is_equal(self, other):
        from pymbolic.rational import Rational
        return self.__class__ == other.__class__ \
               and (self.numerator == other.numerator) \
               and (self.denominator == other.denominator)

    mapper_method = intern("map_remainder")




class Power(Expression):
    def __init__(self, base, exponent):
        self.base = base
        self.exponent = exponent

    def __getinitargs__(self):
        return self.base, self.exponent

    def is_equal(self, other):
        return isinstance(other, Power) \
               and (self.base == other.base) \
               and (self.exponent == other.exponent)

    def get_hash(self):
        return hash((self.__class__, self.base, self.exponent))

    mapper_method = intern("map_power")




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

    def get_hash(self):
        return hash((self.__class__, self.children))

    mapper_method = intern("map_vector")




class CommonSubexpression(Expression):
    def __init__(self, child, prefix=None):
        self.child = child
        self.prefix = prefix

    def __getinitargs__(self):
        return (self.child, self.prefix)

    def get_hash(self):
        return hash((self.__class__, self.child))

    def is_equal(self, other):
        return (other.__class__ == self.__class__
                and other.child == self.child)

    def get_extra_properties(self):
        return {}

    mapper_method = intern("map_common_subexpression")





class IfPositive(Expression):
    def __init__(self, criterion, then, else_):
        self.criterion = criterion
        self.then = then
        self.else_ = else_

    def __getinitargs__(self):
        return self.criterion, self.then, self.else_

    def is_equal(self, other):
        return (isinstance(other, IfPositive)
                and self.criterion == other.criterion
                and self.then == other.then
                and self.else_ == other.else_)

    def get_hash(self):
        return hash((
                self.__class__,
                self.criterion,
                self.then,
                self.else_))

    mapper_method = intern("map_if_positive")




class _MinMaxBase(Expression):
    def __init__(self, children):
        self.children = children

    def __getinitargs__(self):
        return self.children

    def is_equal(self, other):
        return (isinstance(other, type(self))
                and self.children == other.children)

    def get_hash(self):
        return hash((type(self), self.children))

class Min(_MinMaxBase):
    mapper_method = intern("map_min")

class Max(_MinMaxBase):
    mapper_method = intern("map_max")




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

        if is_zero(item):
            return 0
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
global VALID_CONSTANT_CLASSES
global VALID_OPERANDS
VALID_CONSTANT_CLASSES = (int, float, complex)
VALID_OPERANDS = (Expression,)

try:
    import numpy
    VALID_CONSTANT_CLASSES += (numpy.number,)
except ImportError:
    pass




def is_constant(value):
    return isinstance(value, VALID_CONSTANT_CLASSES)

def is_valid_operand(value):
    return isinstance(value, VALID_OPERANDS) or is_constant(value)




def register_constant_class(class_):
    global VALID_CONSTANT_CLASSES

    VALID_CONSTANT_CLASSES += (class_,)

def unregister_constant_class(class_):
    global VALID_CONSTANT_CLASSES

    tmp = list(VALID_CONSTANT_CLASSES)
    tmp.remove(class_)
    VALID_CONSTANT_CLASSES = tuple(tmp)




def is_nonzero(value):
    try:
        return bool(value)
    except ValueError:
        return True

def is_zero(value):
    return not is_nonzero(value)



