from __future__ import division, absolute_import

__copyright__ = "Copyright (C) 2009-2013 Andreas Kloeckner"

__license__ = """
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import pymbolic.traits as traits

import six
from six.moves import range, zip, intern

__doc__ = """
Expression base class
---------------------

.. autoclass:: Expression

Sums, products and such
-----------------------

.. autoclass:: Variable
    :undoc-members:
    :members: mapper_method

.. autoclass:: Call
    :undoc-members:
    :members: mapper_method

.. autoclass:: CallWithKwargs
    :undoc-members:
    :members: mapper_method

.. autoclass:: Subscript
    :undoc-members:
    :members: mapper_method

.. autoclass:: Lookup
    :undoc-members:
    :members: mapper_method

.. autoclass:: Sum
    :undoc-members:
    :members: mapper_method

.. autoclass:: Product
    :undoc-members:
    :members: mapper_method

.. autoclass:: Quotient
    :undoc-members:
    :members: mapper_method

.. autoclass:: FloorDiv
    :undoc-members:
    :members: mapper_method

.. autoclass:: Remainder
    :undoc-members:
    :members: mapper_method

.. autoclass:: Power
    :undoc-members:
    :members: mapper_method

Shift operators
---------------

.. autoclass:: LeftShift
    :undoc-members:
    :members: mapper_method

.. autoclass:: RightShift
    :undoc-members:
    :members: mapper_method

Bitwise operators
-----------------

.. autoclass:: BitwiseNot
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseOr
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseXor
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseAnd
    :undoc-members:
    :members: mapper_method

Comparisons and logic
---------------------

.. autoclass:: Comparison
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalNot
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalAnd
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalOr
    :undoc-members:
    :members: mapper_method

.. autoclass:: If
    :undoc-members:
    :members: mapper_method

Code generation helpers
-----------------------

.. autoclass:: CommonSubexpression
    :undoc-members:
    :members: mapper_method

.. autoclass:: cse_scope
.. autofunction:: make_common_subexpression

Helper functions
----------------

.. autofunction:: is_zero
.. autofunction:: is_constant
.. autofunction:: register_constant_class
.. autofunction:: unregister_constant_class
.. autofunction:: variables

Interaction with :mod:`numpy` arrays
------------------------------------

:mod:`numpy.ndarray` instances are supported anywhere in an expression.
In particular, :mod:`numpy` object arrays are useful for capturing
vectors and matrices of :mod:`pymbolic` objects.

.. autofunction:: make_sym_vector
.. autofunction:: make_sym_array
"""


def disable_subscript_by_getitem():
    # The issue that was addressed by this could be fixed
    # in a much less ham-fisted manner, and thus this has been
    # made a no-op.
    #
    # See
    # https://github.com/inducer/pymbolic/issues/4
    pass


class Expression(object):
    """Superclass for parts of a mathematical expression. Overrides operators
    to implicitly construct :class:`Sum`, :class:`Product` and other expressions.

    Expression objects are immutable.

    .. attribute:: a

    .. attribute:: attr

    .. attribute:: mapper_method

        The :class:`pymbolic.mapper.Mapper` method called for objects of
        this type.

    .. method:: __getitem__

    .. automethod:: stringifier

    .. automethod:: __eq__
    .. automethod:: __hash__
    .. automethod:: __str__
    .. automethod:: __repr__

    .. automethod:: __repr__

    .. rubric:: Logical operator constructors

    .. automethod:: not_
    .. automethod:: and_
    .. automethod:: or_

    .. rubric:: Comparison constructors

    .. automethod:: eq
    .. automethod:: ne
    .. automethod:: lt
    .. automethod:: le
    .. automethod:: gt
    .. automethod:: ge
    """

    # {{{ arithmetic

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

        if is_zero(other):  # exponent zero
            return 1
        elif is_zero(other-1):  # exponent one
            return self
        return Power(self, other)

    def __rpow__(self, other):
        assert is_constant(other)

        if is_zero(other):  # base zero
            return 0
        elif is_zero(other-1):  # base one
            return 1
        return Power(other, self)

    # }}}

    # {{{ shifts

    def __lshift__(self, other):
        return LeftShift(self, other)

    def __rlshift__(self, other):
        return LeftShift(other, self)

    def __rshift__(self, other):
        return RightShift(self, other)

    def __rrshift__(self, other):
        return RightShift(other, self)

    # }}}

    # {{{ bitwise operators

    def __inv__(self):
        return BitwiseNot(self)

    def __or__(self, other):
        return BitwiseOr((self, other))

    def __ror__(self, other):
        return BitwiseOr((other, self))

    def __xor__(self, other):
        return BitwiseXor((self, other))

    def __rxor__(self, other):
        return BitwiseXor((other, self))

    def __and__(self, other):
        return BitwiseAnd((self, other))

    def __rand__(self, other):
        return BitwiseAnd((other, self))

    # }}}

    # {{{ misc

    def __neg__(self):
        return -1*self

    def __call__(self, *args, **kwargs):
        if kwargs:
            return CallWithKwargs(self, args, kwargs)
        else:
            return Call(self, args)

    def index(self, subscript):
        """Return an expression representing ``self[subscript]``.

        .. versionadded:: 2014.3
        """

        if subscript == ():
            return self
        else:
            return Subscript(self, subscript)

    __getitem__ = index

    def attr(self, name):
        """Return a :class:`Lookup` for *name* in *self*.
        """
        return Lookup(self, name)

    @property
    def a(self):
        """Provide a spelling ``expr.a.name`` for encoding attribute lookup.
        """
        class AttributeLookupCreator(object):
            def __init__(self, aggregate):
                self.aggregate = aggregate

            def __getattr__(self, name):
                return Lookup(self.aggregate, name)

        return AttributeLookupCreator(self)

    def __float__(self):
        from pymbolic.mapper.evaluator import evaluate_to_float
        return evaluate_to_float(self)

    def stringifier(self):
        """Return a :class:`pymbolic.mapper.Mapper` class used to yield
        a human-readable representation of *self*. Usually a subclass
        of :class:`pymbolic.mapper.stringifier.StringifyMapper`.
        """
        from pymbolic.mapper.stringifier import StringifyMapper
        return StringifyMapper

    def __str__(self):
        """Use the :meth:`stringifier` to return a human-readable
        string representation of *self*.
        """

        from pymbolic.mapper.stringifier import PREC_NONE
        return self.stringifier()()(self, PREC_NONE)

    def __repr__(self):
        """Provides a default :func:`repr` based on
        the Python pickling interface :meth:`__getinitargs__`.
        """
        initargs_str = ", ".join(repr(i) for i in self.__getinitargs__())

        return "%s(%s)" % (self.__class__.__name__, initargs_str)

    # }}}

    # {{{ hash/equality interface

    def __eq__(self, other):
        """Provides equality testing with quick positive and negative paths
        based on :func:`id` and :meth:`__hash__`.

        Subclasses should generally not override this method, but instead
        provide an implementation of :meth:`is_equal`.
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
        provide an implementation of :meth:`get_hash`.
        """
        try:
            return self.hash_value
        except AttributeError:
            self.hash_value = self.get_hash()
            return self.hash_value

    def __getstate__(self):
        return self.__getinitargs__()

    def __setstate__(self, state):
        # Can't use trivial pickling: hash_value cache must stay unset
        assert len(self.init_arg_names) == len(state)
        for name, value in zip(self.init_arg_names, state):
            setattr(self, name, value)

    # }}}

    # {{{ hash/equality backend

    def is_equal(self, other):
        return (type(other) == type(self)
                and self.__getinitargs__() == other.__getinitargs__())

    def get_hash(self):
        return hash((type(self).__name__,) + self.__getinitargs__())

    # }}}

    # {{{ logical op constructors

    def not_(self):
        """Return *self* wrapped in a :class:`LogicalNot.

        .. versionadded:: 2015.2
        """
        return LogicalNot(self)

    def and_(self, other):
        """Return :class:`LogicalAnd` between *self* and *other*.

        .. versionadded:: 2015.2
        """
        return LogicalAnd((self, other))

    def or_(self, other):
        """Return :class:`LogicalOr` between *self* and *other*.

        .. versionadded:: 2015.2
        """
        return LogicalOr((self, other))

    # }}}

    # {{{ comparison constructors

    def eq(self, other):
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, "==", other)

    def ne(self, other):
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, "!=", other)

    def le(self, other):
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, "<=", other)

    def lt(self, other):
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, "<", other)

    def ge(self, other):
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, ">=", other)

    def gt(self, other):
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, ">", other)

    # }}}

    # {{{ prevent less / greater comparisons

    # /!\ Don't be tempted to resolve these to Comparison.

    def __le__(self, other):
        raise TypeError("expressions don't have an order")

    def __lt__(self, other):
        raise TypeError("expressions don't have an order")

    def __ge__(self, other):
        raise TypeError("expressions don't have an order")

    def __gt__(self, other):
        raise TypeError("expressions don't have an order")

    # }}}

    def __iter__(self):
        # prevent infinite loops (e.g. when inseserting into numpy arrays)
        raise TypeError("expression types are not iterable")


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
    """
    .. attribute:: name
    """
    init_arg_names = ("name",)

    def __init__(self, name):
        self.name = intern(name)

    def __getinitargs__(self):
        return self.name,

    def __lt__(self, other):
        if isinstance(other, Variable):
            return self.name.__lt__(other.name)
        else:
            return NotImplemented

    def __setstate__(self, val):
        super(Variable, self).__setstate__(val)

        self.name = intern(self.name)

    mapper_method = intern("map_variable")


class Wildcard(Leaf):
    def __getinitargs__(self):
        return ()

    mapper_method = intern("map_wildcard")


class FunctionSymbol(AlgebraicLeaf):
    """Represents the name of a function.

    May optionally have an `arg_count` attribute, which will
    allow `Call` to check the number of arguments.
    """

    def __getinitargs__(self):
        return ()

    mapper_method = intern("map_function_symbol")


# {{{ structural primitives

class Call(AlgebraicLeaf):
    """A function invocation.

    .. attribute:: function

        A :class:`Expression` that evaluates to a function.

    .. attribute:: parameters

        A :class:`tuple` of positional paramters, each element
        of which is a :class:`Expression` or a constant.

    """

    init_arg_names = ("function", "parameters",)

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

    mapper_method = intern("map_call")


class CallWithKwargs(AlgebraicLeaf):
    """A function invocation with keyword arguments.

    .. attribute:: function

        A :class:`Expression` that evaluates to a function.

    .. attribute:: parameters

        A :class:`tuple` of positional paramters, each element
        of which is a :class:`Expression` or a constant.

    .. attribute:: kw_parameters

        A dictionary mapping names to arguments, , each
        of which is a :class:`Expression` or a constant,
        or an equivalent value accepted by the :class:`dict`
        constructor.
    """

    init_arg_names = ("function", "parameters", "kw_parameters")

    def __init__(self, function, parameters, kw_parameters):
        self.function = function
        self.parameters = parameters

        if isinstance(kw_parameters, dict):
            self.kw_parameters = kw_parameters
        else:
            self.kw_parameters = dict(kw_parameters)

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
        return (self.function,
                self.parameters,
                tuple(sorted(
                    list(self.kw_parameters.items()),
                    key=lambda item: item[0])))

    mapper_method = intern("map_call_with_kwargs")


class Subscript(AlgebraicLeaf):
    """An array subscript.

    .. attribute:: aggregate
    .. attribute:: index
    .. attribute:: index_tuple

        Return :attr:`index` wrapped in a single-element tuple, if it is not already
        a tuple.
    """

    init_arg_names = ("aggregate", "index",)

    def __init__(self, aggregate, index):
        self.aggregate = aggregate
        self.index = index

    def __getinitargs__(self):
        return self.aggregate, self.index

    @property
    def index_tuple(self):
        if isinstance(self.index, tuple):
            return self.index
        else:
            return (self.index,)

    mapper_method = intern("map_subscript")


class Lookup(AlgebraicLeaf):
    """Access to an attribute of an *aggregate*, such as an
    attribute of a class.
    """

    init_arg_names = ("aggregate", "name",)

    def __init__(self, aggregate, name):
        self.aggregate = aggregate
        self.name = name

    def __getinitargs__(self):
        return self.aggregate, self.name

    mapper_method = intern("map_lookup")

# }}}


# {{{ arithmetic primitives

class _MultiChildExpression(Expression):
    init_arg_names = ("children",)

    def __init__(self, children):
        assert isinstance(children, tuple)

        self.children = children

    def __getinitargs__(self):
        return self.children,


class Sum(_MultiChildExpression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

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

    def __bool__(self):
        if len(self.children) == 0:
            return True
        elif len(self.children) == 1:
            return bool(self.children[0])
        else:
            # FIXME: Right semantics?
            return True

    __nonzero__ = __bool__

    mapper_method = intern("map_sum")


class Product(_MultiChildExpression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

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

    def __bool__(self):
        for i in self.children:
            if is_zero(i):
                return False
        return True

    __nonzero__ = __bool__

    mapper_method = intern("map_product")


class QuotientBase(Expression):
    init_arg_names = ("numerator", "denominator",)

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

    def __bool__(self):
        return bool(self.numerator)

    __nonzero__ = __bool__


class Quotient(QuotientBase):
    """
    .. attribute:: numerator
    .. attribute:: denominator
    """

    def is_equal(self, other):
        from pymbolic.rational import Rational
        return isinstance(other, (Rational, Quotient)) \
               and (self.numerator == other.numerator) \
               and (self.denominator == other.denominator)

    mapper_method = intern("map_quotient")


class FloorDiv(QuotientBase):
    """
    .. attribute:: numerator
    .. attribute:: denominator
    """

    mapper_method = intern("map_floor_div")


class Remainder(QuotientBase):
    """
    .. attribute:: numerator
    .. attribute:: denominator
    """

    mapper_method = intern("map_remainder")


class Power(Expression):
    """
    .. attribute:: base
    .. attribute:: exponent
    """

    init_arg_names = ("base", "exponent",)

    def __init__(self, base, exponent):
        self.base = base
        self.exponent = exponent

    def __getinitargs__(self):
        return self.base, self.exponent

    mapper_method = intern("map_power")

# }}}


# {{{ shift operators

class _ShiftOperator(Expression):
    init_arg_names = ("shiftee", "shift",)

    def __init__(self, shiftee, shift):
        self.shiftee = shiftee
        self.shift = shift

    def __getinitargs__(self):
        return self.shiftee, self.shift


class LeftShift(_ShiftOperator):
    """
    .. attribute:: shiftee
    .. attribute:: shift
    """

    mapper_method = intern("map_left_shift")


class RightShift(_ShiftOperator):
    """
    .. attribute:: shiftee
    .. attribute:: shift
    """

    mapper_method = intern("map_right_shift")

# }}}


# {{{ bitwise operators

class BitwiseNot(Expression):
    """
    .. attribute:: child
    """

    init_arg_names = ("child",)

    def __init__(self, child):
        self.child = child

    def __getinitargs__(self):
        return (self.child,)

    mapper_method = intern("map_bitwise_not")


class BitwiseOr(_MultiChildExpression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    mapper_method = intern("map_bitwise_or")


class BitwiseXor(_MultiChildExpression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    mapper_method = intern("map_bitwise_xor")


class BitwiseAnd(_MultiChildExpression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    mapper_method = intern("map_bitwise_and")

# }}}


# {{{ comparisons, logic, conditionals

class Comparison(Expression):
    """
    .. attribute:: left
    .. attribute:: operator

        One of ``[">", ">=", "==", "!=", "<", "<="]``.

    .. attribute:: right

    .. note::

        Unlike other expressions, comparisons are not implicitly constructed by
        comparing :class:`Expression` objects. See :meth:`Expression.eq`.
    """

    init_arg_names = ("left", "operator", "right")

    def __init__(self, left, operator, right):
        self.left = left
        self.right = right
        if operator not in [">", ">=", "==", "!=", "<", "<="]:
            raise RuntimeError("invalid operator")
        self.operator = operator

    def __getinitargs__(self):
        return self.left, self.operator, self.right

    mapper_method = intern("map_comparison")


class LogicalNot(Expression):
    """
    .. attribute:: child
    """

    init_arg_names = ("child",)

    def __init__(self, child):
        self.child = child

    def __getinitargs__(self):
        return (self.child,)

    mapper_method = intern("map_logical_not")


class LogicalOr(_MultiChildExpression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    mapper_method = intern("map_logical_or")


class LogicalAnd(_MultiChildExpression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    mapper_method = intern("map_logical_and")


class If(Expression):
    """
    .. attribute:: condition
    .. attribute:: then
    .. attribute:: else_
    """

    init_arg_names = ("condition", "then", "else_")

    def __init__(self, condition, then, else_):
        self.condition = condition
        self.then = then
        self.else_ = else_

    def __getinitargs__(self):
        return self.condition, self.then, self.else_

    mapper_method = intern("map_if")


class IfPositive(Expression):
    init_arg_names = ("criterion", "then", "else_")

    def __init__(self, criterion, then, else_):
        from warnings import warn
        warn("IfPositive is deprecated, use If( ... >0)", DeprecationWarning,
                stacklevel=2)

        self.criterion = criterion
        self.then = then
        self.else_ = else_

    def __getinitargs__(self):
        return self.criterion, self.then, self.else_

    mapper_method = intern("map_if_positive")


class _MinMaxBase(Expression):
    init_arg_names = ("children",)

    def __init__(self, children):
        self.children = children

    def __getinitargs__(self):
        return (self.children,)


class Min(_MinMaxBase):
    mapper_method = intern("map_min")


class Max(_MinMaxBase):
    mapper_method = intern("map_max")

# }}}


# {{{ misc stuff

class Vector(Expression):
    """An immutable sequence that you can compute with."""

    init_arg_names = ("children",)

    def __init__(self, children):
        assert isinstance(children, tuple)
        self.children = children

        from warnings import warn
        warn("pymbolic vectors are deprecated in favor of either "
                "(a) numpy object arrays and "
                "(b) pymbolic.geometric_algebra.MultiVector "
                "(depending on the required semantics)",
                DeprecationWarning)

    def __bool__(self):
        for i in self.children:
            if is_nonzero(i):
                return False
        return True

    __nonzero__ = __bool__

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
            raise ValueError("can't add values of differing lengths")
        return Vector(tuple(x+y for x, y in zip(self, other)))

    def __radd__(self, other):
        if len(other) != len(self):
            raise ValueError("can't add values of differing lengths")
        return Vector(tuple(y+x for x, y in zip(self, other)))

    def __sub__(self, other):
        if len(other) != len(self):
            raise ValueError("can't subtract values of differing lengths")
        return Vector(tuple(x-y for x, y in zip(self, other)))

    def __rsub__(self, other):
        if len(other) != len(self):
            raise ValueError("can't subtract values of differing lengths")
        return Vector(tuple(y-x for x, y in zip(self, other)))

    def __mul__(self, other):
        return Vector(tuple(x*other for x in self))

    def __rmul__(self, other):
        return Vector(tuple(other*x for x in self))

    def __div__(self, other):
        import operator
        return Vector(tuple(operator.div(x, other) for x in self))

    def __truediv__(self, other):
        import operator
        return Vector(tuple(operator.truediv(x, other) for x in self))

    def __floordiv__(self, other):
        return Vector(tuple(x//other for x in self))

    def __getinitargs__(self):
        return self.children

    mapper_method = intern("map_vector")


class cse_scope:  # noqa
    """Determines the lifetime for the saved value of a :class:`CommonSubexpression`.

    .. attribute:: EVALUATION

        The evaluated result lives for the duration of the evaluation of the
        current expression and is discarded thereafter.

    .. attribute:: EXPRESSION

        The evaluated result lives for the lifetime of the current expression
        (across multiple evaluations with multiple parameters) and is discarded
        when the expression is.

    .. attribute:: GLOBAL

        The evaluated result lives until the execution context dies.
    """

    EVALUATION = "pymbolic_eval"
    EXPRESSION = "pymbolic_expr"
    GLOBAL = "pymbolic_global"


class CommonSubexpression(Expression):
    """A helper for code generation and caching. Denotes a subexpression that
    should only be evaluated once. If, in code generation, it is assigned to
    a variable, a name starting with :attr:`prefix` should be used.

    .. attribute:: child
    .. attribute:: prefix
    .. attribute:: scope

        One of the values in :class:`cse_scope`. See there for meaning.

    See :class:`pymbolic.mapper.c_code.CCodeMapper` for an example.
    """

    init_arg_names = ("child", "prefix", "scope")

    def __init__(self, child, prefix=None, scope=None):
        """
        :arg scope: Defaults to :attr:`cse_scope.EVALUATION` if given as *None*.
        """
        if scope is None:
            scope = cse_scope.EVALUATION

        self.child = child
        self.prefix = prefix
        self.scope = scope

    def __getinitargs__(self):
        return (self.child, self.prefix, self.scope)

    def get_extra_properties(self):
        """Return a dictionary of extra kwargs to be passed to the
        constructor from the identity mapper.

        This allows derived classes to exist without having to
        extend every mapper that processes them.
        """

        return {}

    mapper_method = intern("map_common_subexpression")


class Substitution(Expression):
    """Work-alike of sympy's Subs."""

    init_arg_names = ("child", "variables", "values")

    def __init__(self, child, variables, values):
        self.child = child
        self.variables = variables
        self.values = values

    def __getinitargs__(self):
        return (self.child, self.variables, self.values)

    mapper_method = intern("map_substitution")


class Derivative(Expression):
    """Work-alike of sympy's Derivative."""

    init_arg_names = ("child", "variables")

    def __init__(self, child, variables):
        self.child = child
        self.variables = variables

    def __getinitargs__(self):
        return (self.child, self.variables)

    mapper_method = intern("map_derivative")


class Slice(Expression):
    """A slice expression as in a[1:7]."""

    init_arg_names = ("children",)

    def __init__(self, children):
        assert isinstance(children, tuple)
        self.children = children

        if len(children) > 3:
            raise ValueError("slice with more than three arguments")

    def __getinitargs__(self):
        return (self.children,)

    def __bool__(self):
        return True

    __nonzero__ = __bool__

    @property
    def start(self):
        if len(self.children) > 1:
            return self.children[0]
        else:
            return None

    @property
    def stop(self):
        if len(self.children) == 1:
            return self.children[0]
        elif len(self.children) > 1:
            return self.children[1]
        else:
            return None

    @property
    def step(self):
        if len(self.children) == 3:
            return self.children[2]
        else:
            return None

    mapper_method = intern("map_slice")

# }}}


# {{{ intelligent factory functions

def make_variable(var_or_string):
    if not isinstance(var_or_string, Expression):
        return Variable(var_or_string)
    else:
        return var_or_string


def subscript(expression, index):
    return Subscript(expression, index)


def flattened_sum(components):
    # flatten any potential sub-sums
    queue = list(components)
    done = []

    while queue:
        item = queue.pop(0)

        if is_zero(item):
            continue

        if isinstance(item, Sum):
            queue += item.children
        else:
            done.append(item)

    if len(done) == 0:
        return 0
    elif len(done) == 1:
        return done[0]
    else:
        return Sum(tuple(done))


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

# }}}


# {{{ tool functions

global VALID_CONSTANT_CLASSES
global VALID_OPERANDS
VALID_CONSTANT_CLASSES = (int, float, complex)
if six.PY2:
    VALID_CONSTANT_CLASSES += (long,)

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


def wrap_in_cse(expr, prefix=None):
    if isinstance(expr, (Variable, Subscript)):
        return expr

    if isinstance(expr, CommonSubexpression):
        if prefix is None:
            return expr
        if expr.prefix is None and type(expr) is CommonSubexpression:
            return CommonSubexpression(expr.child, prefix)

        # existing prefix wins
        return expr

    else:
        return CommonSubexpression(expr, prefix)


def make_common_subexpression(field, prefix=None, scope=None):
    """Wrap *field* in a :class:`CommonSubexpression` with
    *prefix*. If *field* is a :mod:`numpy` object array,
    each individual entry is instead wrapped. If *field* is a
    :class:`pymbolic.geometric_algebra.MultiVector`, each
    coefficient is individually wrapped.

    See :class:`CommonSubexpression` for the meaning of *prefix*
    and *scope*.
    """

    if isinstance(field, CommonSubexpression) and (
            scope is None or scope == cse_scope.EVALUATION
            or field.scope == scope):
        # Don't re-wrap
        return field

    try:
        from pytools.obj_array import log_shape
    except ImportError:
        have_obj_array = False
    else:
        have_obj_array = True

    if have_obj_array:
        ls = log_shape(field)

    from pymbolic.geometric_algebra import MultiVector
    if isinstance(field, MultiVector):
        new_data = {}
        for bits, coeff in six.iteritems(field.data):
            if prefix is not None:
                blade_str = field.space.blade_bits_to_str(bits, "")
                component_prefix = prefix+"_"+blade_str
            else:
                component_prefix = None

            new_data[bits] = make_common_subexpression(
                    coeff, component_prefix, scope)

        return MultiVector(new_data, field.space)

    elif have_obj_array and ls != ():
        from pytools import indices_in_shape
        result = numpy.zeros(ls, dtype=object)

        for i in indices_in_shape(ls):
            if prefix is not None:
                component_prefix = prefix+"_".join(str(i_i) for i_i in i)
            else:
                component_prefix = None

            if is_constant(field[i]):
                result[i] = field[i]
            else:
                result[i] = make_common_subexpression(
                        field[i], component_prefix, scope)

        return result
    else:
        if is_constant(field):
            return field
        else:
            return CommonSubexpression(field, prefix, scope)


def make_sym_vector(name, components, var_factory=None):
    """Return an object array of *components* subscripted
    :class:`Variable` (or subclass) instances.

    :arg components: The number of components in the vector.
    :arg var_factory: The :class:`Variable` subclass to use for instantiating
        the scalar variables.
    """
    if var_factory is None:
        var_factory = Variable

    if isinstance(components, int):
        components = list(range(components))

    from pytools.obj_array import join_fields
    vfld = var_factory(name)
    return join_fields(*[vfld.index(i) for i in components])


def make_sym_array(name, shape, var_factory=None):
    if var_factory is None:
        var_factory = Variable

    vfld = var_factory(name)
    if shape == ():
        return vfld

    import numpy as np
    result = np.zeros(shape, dtype=object)
    from pytools import indices_in_shape
    for i in indices_in_shape(shape):
        result[i] = vfld.index(i)

    return result


def variables(s):
    """Return a list of variables for each (space-delimited) identifier
    in *s*.
    """
    return [Variable(s_i) for s_i in s.split() if s_i]

# }}}


# vim: foldmethod=marker
