from __future__ import annotations


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

from dataclasses import dataclass, fields
from sys import intern
from typing import Any, Callable, ClassVar, Mapping, Tuple, Union
from warnings import warn

import pymbolic.traits as traits


# FIXME: This is a lie. Many more constant types (e.g. numpy and such)
# are in practical use and completely fine. We cannot really add in numpy
# as a special case (because pymbolic doesn't have a hard numpy dependency),
# and there isn't a usable numerical tower that we could rely on. As such,
# code abusing what constants are allowable will have to type-ignore those
# statements. Better ideas would be most welcome.
#
# References:
# https://github.com/python/mypy/issues/3186
# https://discuss.python.org/t/numeric-generics-where-do-we-go-from-pep-3141-and-present-day-mypy/17155/14
_ConstantT = Union[int, float, complex]
ExpressionT = Union[_ConstantT, "Expression", Tuple["ExpressionT", ...]]


__doc__ = """
Expression base class
---------------------

.. autoclass:: Expression

.. class:: ExpressionT

    A type that can be used in type annotations whenever an expression
    is desired. A :class:`typing.Union` of :class:`Expression` and
    built-in scalar types.

.. autofunction:: augment_expression_dataclass

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
.. autofunction:: flattened_sum
.. autofunction:: flattened_product
.. autofunction:: register_constant_class
.. autofunction:: unregister_constant_class
.. autofunction:: variables

Interaction with :mod:`numpy` arrays
------------------------------------

:class:`numpy.ndarray` instances are supported anywhere in an expression.
In particular, :mod:`numpy` object arrays are useful for capturing
vectors and matrices of :mod:`pymbolic` objects.

.. autofunction:: make_sym_vector
.. autofunction:: make_sym_array

Constants
---------

.. autoclass:: NaN
    :undoc-members:
    :members: mapper_method
"""


# The upper bound for the number of nodes printed when repr
# is called on a pymbolic object.
SAFE_REPR_LIMIT = 10


def disable_subscript_by_getitem():
    # The issue that was addressed by this could be fixed
    # in a much less ham-fisted manner, and thus this has been
    # made a no-op.
    #
    # See
    # https://github.com/inducer/pymbolic/issues/4
    pass


class Expression:
    """Superclass for parts of a mathematical expression. Overrides operators
    to implicitly construct :class:`Sum`, :class:`Product` and other expressions.

    Expression objects are immutable.

    .. versionchanged:: 2022.2

        `PEP 634 <https://peps.python.org/pep-0634/>`__-style pattern matching
        is now supported when Pymbolic is used under Python 3.10.

    .. attribute:: a

    .. attribute:: attr

    .. attribute:: mapper_method

        The :class:`pymbolic.mapper.Mapper` method called for objects of
        this type.

    .. method:: __getitem__

    .. method:: __getinitargs__

    .. automethod:: make_stringifier

    .. automethod:: __eq__
    .. automethod:: __hash__
    .. automethod:: __str__
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

    # {{{ init arg names (override by subclass)

    def __getinitargs__(self):
        raise NotImplementedError

    @classmethod
    @property
    def __match_args__(cls):
        return cls.init_arg_names

    @property
    def init_arg_names(self):
        raise NotImplementedError

    # }}}

    # {{{ arithmetic

    def __add__(self, other):
        if not is_valid_operand(other):
            return NotImplemented
        if is_nonzero(other):
            if self:
                if isinstance(other, Sum):
                    return Sum((self, *other.children))
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
            return 0
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

    def __invert__(self):
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

    def __pos__(self):
        return self

    def __call__(self, *args, **kwargs):
        if kwargs:
            from immutabledict import immutabledict
            return CallWithKwargs(self, args, immutabledict(kwargs))
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
        class AttributeLookupCreator:
            def __init__(self, aggregate):
                self.aggregate = aggregate

            def __getattr__(self, name):
                return Lookup(self.aggregate, name)

        return AttributeLookupCreator(self)

    def __float__(self):
        from pymbolic.mapper.evaluator import evaluate_to_float
        return evaluate_to_float(self)

    def make_stringifier(self, originating_stringifier=None):
        """Return a :class:`pymbolic.mapper.Mapper` instance that can
        be used to generate a human-readable representation of *self*. Usually
        a subclass of :class:`pymbolic.mapper.stringifier.StringifyMapper`.

        :arg originating_stringifier: If provided, the newly created
            stringifier should carry forward attributes and settings of
            *originating_stringifier*.
        """
        from pymbolic.mapper.stringifier import StringifyMapper
        return StringifyMapper()

    def __str__(self):
        """Use the :meth:`make_stringifier` to return a human-readable
        string representation of *self*.
        """

        from pymbolic.mapper.stringifier import PREC_NONE
        return self.make_stringifier()(self, PREC_NONE)

    def _safe_repr(self, limit=None):
        if limit is None:
            limit = SAFE_REPR_LIMIT

        if limit <= 0:
            return "..."

        def strify_child(child, limit):
            if isinstance(child, tuple):
                # Make sure limit propagates at least through tuples

                return "({}{})".format(
                        ", ".join(strify_child(i, limit-1) for i in child),
                        "," if len(child) == 1 else "")

            elif isinstance(child, Expression):
                return child._safe_repr(limit=limit-1)
            else:
                return repr(child)

        initargs_str = ", ".join(
                strify_child(i, limit-1)
                for i in self.__getinitargs__())

        return f"{self.__class__.__name__}({initargs_str})"

    def __repr__(self):
        """Provides a default :func:`repr` based on
        the Python pickling interface :meth:`__getinitargs__`.
        """
        return self._safe_repr()

    # }}}

    # {{{ hash/equality interface

    def __eq__(self, other):
        """Provides equality testing with quick positive and negative paths
        based on :func:`id` and :meth:`__hash__`.
        """
        from warnings import warn
        warn(f"Expression.__eq__ is used by {self.__class__}. This is deprecated. "
             "Use equality comparison supplied by augment_expression_dataclass "
             "instead. "
             "This will stop working in 2025.",
             DeprecationWarning, stacklevel=2)
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
        """
        from warnings import warn
        warn(f"Expression.__hash__ is used by {self.__class__}. This is deprecated. "
             "Use hash functions supplied by augment_expression_dataclass instead. "
             "This will stop working in 2025.",
             DeprecationWarning, stacklevel=2)

        try:
            return self._hash_value
        except AttributeError:
            self._hash_value = self.get_hash()
            return self._hash_value

    def __getstate__(self):
        return self.__getinitargs__()

    def __setstate__(self, state):
        # Can't use trivial pickling: _hash_value cache must stay unset
        assert len(self.init_arg_names) == len(state), type(self)
        for name, value in zip(self.init_arg_names, state):
            object.__setattr__(self, name, value)

    # }}}

    # {{{ hash/equality backend

    def is_equal(self, other):
        return (type(other) is type(self)
                and self.__getinitargs__() == other.__getinitargs__())

    def get_hash(self):
        return hash((type(self).__name__, *self.__getinitargs__()))

    # }}}

    # {{{ logical op constructors

    def not_(self):
        """Return *self* wrapped in a :class:`LogicalNot`.

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

    def __abs__(self):
        return Call(Variable("abs"), (self,))

    def __iter__(self):
        # prevent infinite loops (e.g. when inserting into numpy arrays)
        raise TypeError("expression types are not iterable")


# {{{ dataclasses support

def augment_expression_dataclass(cls: type[Expression]) -> type[Expression]:
    """A class decorator for :func:`dataclasses.dataclass`-derived
    :class:`Expression` nodes. It adds cached hashing, equality comparisons
    with ``self is other`` shortcuts as well as some methods/attributes
    for backward compatibility (e.g. ``__getinitargs__``, ``init_arg_names``)
    """
    attr_tuple = ", ".join(f"self.{fld.name}" for fld in fields(cls))
    if attr_tuple:
        attr_tuple = f"({attr_tuple},)"
    else:
        attr_tuple = "()"

    fld_name_tuple = ", ".join(f"'{fld.name}'" for fld in fields(cls))
    if fld_name_tuple:
        fld_name_tuple = f"({fld_name_tuple},)"
    else:
        fld_name_tuple = "()"

    comparison = " and ".join(
            f"self.{fld.name} == other.{fld.name}"
            for fld in fields(cls))

    if not comparison:
        comparison = "True"

    from pytools.codegen import remove_common_indentation
    augment_code = remove_common_indentation(
        f"""
        from warnings import warn

        # def {cls.__name__}__post_init__(self):
        #     if hasattr(self, "name"):
        #         self.name = intern(self.name)

        # cls.__post_init__ = {cls.__name__}__post_init__


        def {cls.__name__}_eq(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return False
            if hash(self) != hash(other):
                return False
            if self.__class__ is not cls and self.init_arg_names != {fld_name_tuple}:
                warn(f"{{self.__class__}} is derived from {cls}, which is now "
                    f"a dataclass. {{self.__class__}} should be converted to being "
                    "a dataclass as well. Non-dataclass subclasses "
                    "will stop working in 2025.",
                    DeprecationWarning)

                return self.is_equal(other)

            return self.__class__ == other.__class__ and {comparison}

        cls.__eq__ = {cls.__name__}_eq


        def {cls.__name__}_hash(self):
            try:
                return self._hash_value
            except AttributeError:
                pass

            if self.__class__ is not cls and self.init_arg_names != {fld_name_tuple}:
                warn(f"{{self.__class__}} is derived from {cls}, which is now "
                    f"a dataclass. {{self.__class__}} should be converted to being "
                    "a dataclass as well. Non-dataclass subclasses "
                    "will stop working in 2025.",
                    DeprecationWarning)

                hash_val = self.get_hash()
            else:
                hash_val = hash({attr_tuple})

            object.__setattr__(self, "_hash_value", hash_val)
            return hash_val

        cls.__hash__ = {cls.__name__}_hash


        def {cls.__name__}_init_arg_names(self):
            warn("__getinitargs__ is deprecated and will be removed in 2025. "
                    "Use dataclasses.fields instead.",
                    DeprecationWarning, stacklevel=2)

            return {fld_name_tuple}

        cls.init_arg_names = property({cls.__name__}_init_arg_names)


        def {cls.__name__}_getinitargs(self):
            warn("__getinitargs__ is deprecated and will be removed in 2025. "
                    "Use dataclasses.fields instead.",
                    DeprecationWarning, stacklevel=2)

            return {attr_tuple}

        cls.__getinitargs__ = {cls.__name__}_getinitargs


        # FIXME Also implement pickling, with fallback
        """)

    exec_dict = {"cls": cls, "_MODULE_SOURCE_CODE": augment_code}
    exec(compile(augment_code,
                 f"<dataclass augmentation code for {cls}>", "exec"),
         exec_dict)

    return cls

# }}}


class AlgebraicLeaf(Expression):
    """An expression that serves as a leaf for arithmetic evaluation.
    This may end up having child nodes still, but they're not reached by
    ways of arithmetic."""
    pass


class Leaf(AlgebraicLeaf):
    """An expression that is irreducible, i.e. has no Expression-type parts
    whatsoever."""
    pass


@augment_expression_dataclass
@dataclass(repr=False)
class Variable(Leaf):
    """
    .. attribute:: name
    """
    name: str

    # def __post_init__(self):
    #     object.__setattr__(self, "name", intern(self.name))

    mapper_method = intern("map_variable")


@augment_expression_dataclass
@dataclass(repr=False)
class Wildcard(Leaf):
    mapper_method = intern("map_wildcard")


@augment_expression_dataclass
@dataclass(repr=False)
class DotWildcard(Leaf):
    """
    A wildcard that can be substituted for a single expression.
    """
    name: str

    mapper_method = intern("map_dot_wildcard")


@augment_expression_dataclass
@dataclass(repr=False)
class StarWildcard(Leaf):
    """
    A wildcard that can be substituted by a sequence of expressions of
    non-negative length.
    """
    name: str

    mapper_method = intern("map_star_wildcard")


@augment_expression_dataclass
@dataclass(repr=False)
class FunctionSymbol(AlgebraicLeaf):
    """Represents the name of a function.

    May optionally have an `arg_count` attribute, which will
    allow `Call` to check the number of arguments.
    """

    mapper_method = intern("map_function_symbol")


# {{{ structural primitives

@augment_expression_dataclass
@dataclass(repr=False)
class Call(AlgebraicLeaf):
    """A function invocation.

    .. attribute:: function

        A :class:`Expression` that evaluates to a function.

    .. attribute:: parameters

        A :class:`tuple` of positional parameters, each element
        of which is a :class:`Expression` or a constant.

    """
    function: ExpressionT
    parameters: tuple[ExpressionT, ...]

    mapper_method = intern("map_call")


@augment_expression_dataclass
@dataclass(repr=False)
class CallWithKwargs(AlgebraicLeaf):
    """A function invocation with keyword arguments.

    .. attribute:: function

        A :class:`Expression` that evaluates to a function.

    .. attribute:: parameters

        A :class:`tuple` of positional parameters, each element
        of which is a :class:`Expression` or a constant.

    .. attribute:: kw_parameters

        A dictionary mapping names to arguments, , each
        of which is a :class:`Expression` or a constant,
        or an equivalent value accepted by the :class:`dict`
        constructor.
    """

    function: ExpressionT
    parameters: tuple[ExpressionT, ...]
    kw_parameters: Mapping[str, ExpressionT]

    mapper_method = intern("map_call_with_kwargs")


@augment_expression_dataclass
@dataclass(repr=False)
class Subscript(AlgebraicLeaf):
    """An array subscript.

    .. attribute:: aggregate
    .. attribute:: index
    .. attribute:: index_tuple

        Return :attr:`index` wrapped in a single-element tuple, if it is not already
        a tuple.
    """
    aggregate: ExpressionT
    index: ExpressionT

    @property
    def index_tuple(self):
        if isinstance(self.index, tuple):
            return self.index
        else:
            return (self.index,)

    mapper_method = intern("map_subscript")


@augment_expression_dataclass
@dataclass(repr=False)
class Lookup(AlgebraicLeaf):
    """Access to an attribute of an *aggregate*, such as an
    attribute of a class.
    """

    aggregate: ExpressionT
    name: str

    mapper_method = intern("map_lookup")

# }}}


# {{{ arithmetic primitives

@augment_expression_dataclass
@dataclass(repr=False)
class Sum(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    children: tuple[ExpressionT, ...]

    def __add__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if isinstance(other, Sum):
            return Sum(self.children + other.children)
        if not other:
            return self
        return Sum((*self.children, other))

    def __radd__(self, other):
        if not is_constant(other):
            return NotImplemented

        if isinstance(other, Sum):
            return Sum(other.children + self.children)
        if not other:
            return self
        return Sum((other, *self.children))

    def __sub__(self, other):
        if not is_valid_operand(other):
            return NotImplemented

        if not other:
            return self
        return Sum((*self.children, -other))

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


@augment_expression_dataclass
@dataclass(repr=False)
class Product(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    children: tuple[ExpressionT, ...]

    def __mul__(self, other):
        if not is_valid_operand(other):
            return NotImplemented
        if isinstance(other, Product):
            return Product(self.children + other.children)
        if is_zero(other):
            return 0
        if is_zero(other-1):
            return self
        return Product((*self.children, other))

    def __rmul__(self, other):
        if not is_constant(other):
            return NotImplemented
        if isinstance(other, Product):
            return Product(other.children + self.children)
        if is_zero(other):
            return 0
        if is_zero(other-1):
            return self
        return Product((other, *self.children))

    def __bool__(self):
        for i in self.children:
            if is_zero(i):
                return False
        return True

    __nonzero__ = __bool__

    mapper_method = intern("map_product")


@augment_expression_dataclass
@dataclass(repr=False)
class QuotientBase(Expression):
    numerator: ExpressionT
    denominator: ExpressionT

    @property
    def num(self):
        return self.numerator

    @property
    def den(self):
        return self.denominator

    def __bool__(self):
        return bool(self.numerator)

    __nonzero__ = __bool__


@augment_expression_dataclass
@dataclass(repr=False)
class Quotient(QuotientBase):
    """
    .. attribute:: numerator
    .. attribute:: denominator
    """

    mapper_method = intern("map_quotient")


@augment_expression_dataclass
@dataclass(repr=False)
class FloorDiv(QuotientBase):
    """
    .. attribute:: numerator
    .. attribute:: denominator
    """

    mapper_method = intern("map_floor_div")


@augment_expression_dataclass
@dataclass(repr=False)
class Remainder(QuotientBase):
    """
    .. attribute:: numerator
    .. attribute:: denominator
    """

    mapper_method = intern("map_remainder")


@augment_expression_dataclass
@dataclass(repr=False)
class Power(Expression):
    """
    .. attribute:: base
    .. attribute:: exponent
    """

    base: ExpressionT
    exponent: ExpressionT

    mapper_method = intern("map_power")

# }}}


# {{{ shift operators

@augment_expression_dataclass
@dataclass(repr=False)
class _ShiftOperator(Expression):
    shiftee: ExpressionT
    shift: ExpressionT


@augment_expression_dataclass
@dataclass(repr=False)
class LeftShift(_ShiftOperator):
    """
    .. attribute:: shiftee
    .. attribute:: shift
    """

    mapper_method = intern("map_left_shift")


@augment_expression_dataclass
@dataclass(repr=False)
class RightShift(_ShiftOperator):
    """
    .. attribute:: shiftee
    .. attribute:: shift
    """

    mapper_method = intern("map_right_shift")

# }}}


# {{{ bitwise operators

@augment_expression_dataclass
@dataclass(repr=False)
class BitwiseNot(Expression):
    """
    .. attribute:: child
    """

    child: ExpressionT

    mapper_method = intern("map_bitwise_not")


@augment_expression_dataclass
@dataclass(repr=False)
class BitwiseOr(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    children: tuple[ExpressionT, ...]

    mapper_method = intern("map_bitwise_or")


@augment_expression_dataclass
@dataclass(repr=False)
class BitwiseXor(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """
    children: tuple[ExpressionT, ...]

    mapper_method = intern("map_bitwise_xor")


@augment_expression_dataclass
@dataclass(repr=False)
class BitwiseAnd(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """
    children: tuple[ExpressionT, ...]

    mapper_method = intern("map_bitwise_and")

# }}}


# {{{ comparisons, logic, conditionals

@augment_expression_dataclass
@dataclass(repr=False)
class Comparison(Expression):
    """
    .. attribute:: left
    .. attribute:: operator

        One of ``[">", ">=", "==", "!=", "<", "<="]``.

    .. attribute:: right

    .. note::

        Unlike other expressions, comparisons are not implicitly constructed by
        comparing :class:`Expression` objects. See :meth:`Expression.eq`.

    .. attribute:: operator_to_name
    .. attribute:: name_to_operator
    """

    left: ExpressionT
    operator: str
    right: ExpressionT

    operator_to_name: ClassVar[dict[str, str]] = {
            "==": "eq",
            "!=": "ne",
            ">=": "ge",
            ">": "gt",
            "<=": "le",
            "<": "lt",
            }
    name_to_operator: ClassVar[dict[str, str]] = {
        name: op for op, name in operator_to_name.items()
    }

    def __post_init__(self):
        # FIXME Yuck, gross
        if self.operator not in self.operator_to_name:
            if self.operator in self.name_to_operator:
                warn("Passing operators by name is deprecated and will stop working "
                     "in 2025. "
                     "Use the name_to_operator class attribute to translate in "
                     "calling code instead.",
                     DeprecationWarning, stacklevel=3)

                object.__setattr__(
                        self, "operator", self.name_to_operator[self.operator])
            else:
                raise RuntimeError(f"invalid operator: '{self.operator}'")

    mapper_method = intern("map_comparison")


@augment_expression_dataclass
@dataclass(repr=False)
class LogicalNot(Expression):
    """
    .. attribute:: child
    """

    child: ExpressionT

    mapper_method = intern("map_logical_not")


@augment_expression_dataclass
@dataclass(repr=False)
class LogicalOr(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """

    children: tuple[ExpressionT, ...]

    mapper_method = intern("map_logical_or")


@augment_expression_dataclass
@dataclass(repr=False)
class LogicalAnd(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """
    children: tuple[ExpressionT, ...]

    mapper_method = intern("map_logical_and")


@augment_expression_dataclass
@dataclass(repr=False)
class If(Expression):
    """
    .. attribute:: condition
    .. attribute:: then
    .. attribute:: else_
    """

    condition: ExpressionT
    then: ExpressionT
    else_: ExpressionT

    mapper_method = intern("map_if")


@augment_expression_dataclass
@dataclass(repr=False)
class Min(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """
    children: tuple[ExpressionT, ...]

    mapper_method = intern("map_min")


@augment_expression_dataclass
@dataclass(repr=False)
class Max(Expression):
    """
    .. attribute:: children

        A :class:`tuple`.
    """
    children: tuple[ExpressionT, ...]

    mapper_method = intern("map_max")

# }}}


# {{{ misc stuff

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


@augment_expression_dataclass
@dataclass(repr=False)
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

    child: ExpressionT
    prefix: str | None = None
    scope: str = cse_scope.EVALUATION

    def __post_init__(self):
        if self.scope is None:
            warn("CommonSubexpression.scope set to None. "
                 "This is deprecated and will stop working in 2024. "
                "Use cse_scope.EVALUATION explicitly instead.",
                 DeprecationWarning, stacklevel=3)
            object.__setattr__(self, "scope", cse_scope.EVALUATION)

    def get_extra_properties(self):
        """Return a dictionary of extra kwargs to be passed to the
        constructor from the identity mapper.

        This allows derived classes to exist without having to
        extend every mapper that processes them.
        """

        return {}

    mapper_method = intern("map_common_subexpression")


@augment_expression_dataclass
@dataclass(repr=False)
class Substitution(Expression):
    """Work-alike of sympy's Subs."""

    child: ExpressionT
    variables: tuple[str, ...]
    values: tuple[ExpressionT, ...]

    mapper_method = intern("map_substitution")


@augment_expression_dataclass
@dataclass(repr=False)
class Derivative(Expression):
    """Work-alike of sympy's Derivative."""

    child: ExpressionT
    variables: tuple[str, ...]

    mapper_method = intern("map_derivative")


@augment_expression_dataclass
@dataclass(repr=False)
class Slice(Expression):
    """A slice expression as in a[1:7]."""

    children: (tuple[()]
        | tuple[ExpressionT]
        | tuple[ExpressionT, ExpressionT]
        | tuple[ExpressionT, ExpressionT, ExpressionT])

    def __bool__(self):
        return True

    __nonzero__ = __bool__

    @property
    def start(self):
        if len(self.children) > 0:
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


@augment_expression_dataclass
@dataclass(repr=False)
class NaN(Expression):
    """
    An expression node representing not-a-number as a floating point number.
    Unlike, :data:`math.nan`, all instances of :class:`NaN` compare equal, as
    one might reasonably expect for program representation. (If this weren't
    so, programs containing NaNs would effectively be unhashable, because they
    don't compare equal to themselves.)

    Note that, in Python, this equality comparison is made *even* more
    complex by `this issue <https://bugs.python.org/issue21873>`__, due
    to which ``np.nan == np.nan`` is *False*, but ``(np.nan,) == (np.nan,)``
    is True.

    .. attribute:: data_type

        The data type used for the actual realization of the constant. Defaults
        to *None*. If given, This must be a callable to which a NaN
        :class:`float` can be passed to obtain a NaN of the yield the desired
        type.  It must also be suitable for use as the second argument of
        :func:`isinstance`.
    """
    data_type: Callable[[float], Any] | None = None

    mapper_method = intern("map_nan")

# }}}


# {{{ intelligent factory functions

def make_variable(var_or_string: Expression | str) -> Variable:
    if isinstance(var_or_string, str):
        return Variable(intern(var_or_string))
    else:
        return var_or_string


def subscript(expression, index):
    return Subscript(expression, index)


def flattened_sum(terms):
    r"""Recursively flattens all the top level :class:`Sum`\ s in *terms*.

    :arg terms: an :class:`~collections.abc.Iterable` of expressions.
    :returns: a :class:`Sum` expression or, if there is only one term in
        the sum, the respective term.
    """
    queue = list(terms)
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


def flattened_product(terms):
    r"""Recursively flattens all the top level :class:`Product`\ s in *terms*.

    This operation does not change the order of the terms in the products, so
    it does not require the product to be commutative.

    :arg terms: an :class:`~collections.abc.Iterable` of expressions.
    :returns: a :class:`Product` expression or, if there is only one term in
        the product, the respective term.
    """
    queue = list(terms)
    done = []

    while queue:
        item = queue.pop(0)

        if is_zero(item):
            return 0
        if is_zero(item - 1):
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
VALID_OPERANDS = (Expression,)

try:
    import numpy
    VALID_CONSTANT_CLASSES += (numpy.number, numpy.bool_)
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
    if value is None:
        raise ValueError("is_nonzero is undefined for None")

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
        import numpy
        have_obj_array = (
            isinstance(field, numpy.ndarray)
            and field.dtype.char == "O")
        logical_shape = (
            field.shape
            if isinstance(field, numpy.ndarray)
            else ())
    except ImportError:
        have_obj_array = False
        logical_shape = ()

    from pymbolic.geometric_algebra import MultiVector
    if isinstance(field, MultiVector):
        new_data = {}
        for bits, coeff in field.data.items():
            if prefix is not None:
                blade_str = field.space.blade_bits_to_str(bits, "")
                component_prefix = prefix+"_"+blade_str
            else:
                component_prefix = None

            new_data[bits] = make_common_subexpression(
                    coeff, component_prefix, scope)

        return MultiVector(new_data, field.space)

    elif have_obj_array and logical_shape != ():
        result = numpy.zeros(logical_shape, dtype=object)
        for i in numpy.ndindex(logical_shape):
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


def make_sym_vector(name, components, var_factory=Variable):
    """Return an object array of *components* subscripted
    :class:`Variable` (or subclass) instances.

    :arg components: Either a list of indices, or an integer representing the
        number of indices.
    :arg var_factory: The :class:`Variable` subclass to
        use for instantiating the scalar variables.

    For example, this creates a vector with three components::

        >>> make_sym_vector("vec", 3)
        array([Subscript(Variable('vec'), 0), Subscript(Variable('vec'), 1),
               Subscript(Variable('vec'), 2)], dtype=object)

    """
    from numbers import Integral
    if isinstance(components, Integral):
        components = list(range(components))

    from pytools.obj_array import flat_obj_array
    vfld = var_factory(name)
    return flat_obj_array(*[vfld.index(i) for i in components])


def make_sym_array(name, shape, var_factory=Variable):
    vfld = var_factory(name)
    if shape == ():
        return vfld

    import numpy as np
    result = np.zeros(shape, dtype=object)
    for i in np.ndindex(shape):
        result[i] = vfld.index(i)

    return result


def variables(s):
    """Return a list of variables for each (space-delimited) identifier
    in *s*.
    """
    return [Variable(s_i) for s_i in s.split() if s_i]

# }}}


# vim: foldmethod=marker
