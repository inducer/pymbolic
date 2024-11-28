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

import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields
from functools import partial
from sys import intern
from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    NoReturn,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
)
from warnings import warn

from immutabledict import immutabledict
from typing_extensions import TypeIs, dataclass_transform

from pytools import module_getattr_for_deprecations

from . import traits
from .typing import ArithmeticExpression, Expression as _Expression, Number, Scalar


if TYPE_CHECKING:
    from _typeshed import DataclassInstance


__doc__ = """
Expression base class
---------------------

.. currentmodule:: pymbolic

.. autoclass:: ExpressionNode

.. autofunction:: expr_dataclass

.. autoclass:: Variable
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

Expressions
-----------

.. currentmodule:: pymbolic.primitives

.. autoclass:: AlgebraicLeaf
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: Leaf
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: Wildcard
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: DotWildcard
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: StarWildcard
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

Function Calls
--------------

.. autoclass:: Call
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: CallWithKwargs
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: Subscript
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: Lookup
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

Sums, products and such
-----------------------

.. autoclass:: Sum
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: Product
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: Min
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: Max
    :show-inheritance:
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
    :show-inheritance:
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
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseOr
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseXor
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: BitwiseAnd
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

Comparisons and logic
---------------------

.. autoclass:: Comparison
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalNot
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalAnd
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: LogicalOr
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: If
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

Slices
----------

.. autoclass:: Slice
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

Code generation helpers
-----------------------

.. autoclass:: CommonSubexpression
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: cse_scope
.. autofunction:: make_common_subexpression

Symbolic derivatives and substitution
-------------------------------------

Inspired by similar functionality in :mod:`sympy`.

.. autoclass:: Substitution
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

.. autoclass:: Derivative
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

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
    :show-inheritance:
    :undoc-members:
    :members: mapper_method

Helper classes
--------------

.. autoclass:: EmptyOK
.. autoclass:: _AttributeLookupCreator

References
----------

.. class:: DataclassInstance

    An instance of a :func:`~dataclasses.dataclass`.

.. class:: ArithmeticExpression

    See :class:`pymbolic.ArithmeticExpression`

.. class:: _T

    A type variable.

.. currentmodule:: numpy

.. class:: bool_

    Deprecated alias for :class:`numpy.bool`.

.. currentmodule:: typing_extensions

.. class:: TypeIs

    See :data:`typing_extensions.TypeIs`.

.. class:: Variable

    See :class:`pymbolic.Variable`.

.. class:: Expression

    See :data:`pymbolic.typing.Expression`.

.. currentmodule:: pymbolic

.. class:: Comparison

    See :class:`pymbolic.primitives.Comparison`.

.. class:: LogicalNot

    See :class:`pymbolic.primitives.LogicalNot`.

.. class:: LogicalAnd

    See :class:`pymbolic.primitives.LogicalAnd`.

.. class:: LogicalOr

    See :class:`pymbolic.primitives.LogicalOr`.

.. class:: Lookup

    See :class:`pymbolic.primitives.Lookup`.
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


# https://stackoverflow.com/a/13624858
class _classproperty(property):  # noqa: N801
    def __get__(self, owner_self: Any, owner_cls: type | None = None) -> Any:
        assert self.fget is not None
        return self.fget(owner_cls)


class _AttributeLookupCreator:
    """Helper used by :attr:`pymbolic.ExpressionNode.a` to create lookups.

    .. automethod:: __getattr__
    """
    def __init__(self, aggregate: _Expression) -> None:
        self.aggregate = aggregate

    def __getattr__(self, name: str) -> Lookup:
        return Lookup(self.aggregate, name)


@dataclass(frozen=True)
class EmptyOK:
    child: _Expression


class ExpressionNode:
    """Superclass for parts of a mathematical expression. Overrides operators
    to implicitly construct :class:`~pymbolic.primitives.Sum`,
    :class:`~pymbolic.primitives.Product` and other expressions.

    Expression objects are immutable.

    .. versionchanged:: 2022.2

        `PEP 634 <https://peps.python.org/pep-0634/>`__-style pattern matching
        is now supported.

    .. autoproperty:: a

    .. automethod:: attr

    .. autoattribute:: mapper_method

        The :class:`pymbolic.mapper.Mapper` method called for objects of
        this type.

    .. automethod:: __getitem__

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

    mapper_method: ClassVar[str]

    # {{{ init arg names (override by subclass)

    def __getinitargs__(self):
        raise NotImplementedError

    @_classproperty
    def __match_args__(cls):  # noqa: N805  # pylint: disable=no-self-argument
        return cls.init_arg_names

    @property
    def init_arg_names(self) -> tuple[str, ...]:
        raise NotImplementedError

    # }}}

    # {{{ arithmetic

    def __add__(self, other: object) -> Sum:
        if not is_arithmetic_expression(other):
            return NotImplemented
        return Sum((self, other))

    def __radd__(self, other: object) -> Sum:
        if not is_arithmetic_expression(other):
            return NotImplemented
        return Sum((other, self))

    def __sub__(self, other: object) -> Sum:
        if not is_arithmetic_expression(other):
            return NotImplemented
        return Sum((self, -other))

    def __rsub__(self, other: object) -> Sum:
        if not is_arithmetic_expression(other):
            return NotImplemented
        return Sum((other, -self))

    def __mul__(self, other: object) -> Product:
        if not is_valid_operand(other):
            return NotImplemented

        return Product((self, other))

    def __rmul__(self, other: object) -> Product:
        if not is_valid_operand(other):
            return NotImplemented

        return Product((other, self))

    def __truediv__(self, other: object) -> Quotient:
        if not is_arithmetic_expression(other):
            return NotImplemented

        return Quotient(self, other)

    def __rtruediv__(self, other: object) -> Quotient:
        if not is_arithmetic_expression(other):
            return NotImplemented

        return Quotient(other, self)

    def __floordiv__(self, other: object) -> FloorDiv:
        if not is_arithmetic_expression(other):
            return NotImplemented

        return FloorDiv(self, other)

    def __rfloordiv__(self, other: object) -> FloorDiv:
        if not is_arithmetic_expression(other):
            return NotImplemented

        return FloorDiv(other, self)

    def __mod__(self, other: object) -> Remainder:
        if not is_arithmetic_expression(other):
            return NotImplemented

        return Remainder(self, other)

    def __rmod__(self, other: object) -> Remainder:
        if not is_arithmetic_expression(other):
            return NotImplemented

        return Remainder(other, self)

    def __pow__(self, other: object) -> Power:
        if not is_arithmetic_expression(other):
            return NotImplemented

        return Power(self, other)

    def __rpow__(self, other: object) -> Power:
        if not is_arithmetic_expression(other):
            return NotImplemented

        return Power(other, self)

    # }}}

    # {{{ shifts

    def __lshift__(self, other: object) -> LeftShift:
        if not is_valid_operand(other):
            return NotImplemented

        return LeftShift(self, other)

    def __rlshift__(self, other: object) -> LeftShift:
        if not is_valid_operand(other):
            return NotImplemented

        return LeftShift(other, self)

    def __rshift__(self, other: object) -> RightShift:
        if not is_valid_operand(other):
            return NotImplemented

        return RightShift(self, other)

    def __rrshift__(self, other: object) -> RightShift:
        if not is_valid_operand(other):
            return NotImplemented

        return RightShift(other, self)

    # }}}

    # {{{ bitwise operators

    def __invert__(self) -> BitwiseNot:
        return BitwiseNot(self)

    def __or__(self, other: object) -> BitwiseOr:
        if not is_valid_operand(other):
            return NotImplemented

        return BitwiseOr((self, other))

    def __ror__(self, other: object) -> BitwiseOr:
        if not is_valid_operand(other):
            return NotImplemented

        return BitwiseOr((other, self))

    def __xor__(self, other: object) -> BitwiseXor:
        if not is_valid_operand(other):
            return NotImplemented

        return BitwiseXor((self, other))

    def __rxor__(self, other: object) -> BitwiseXor:
        if not is_valid_operand(other):
            return NotImplemented

        return BitwiseXor((other, self))

    def __and__(self, other: object) -> BitwiseAnd:
        if not is_valid_operand(other):
            return NotImplemented

        return BitwiseAnd((self, other))

    def __rand__(self, other: object) -> BitwiseAnd:
        if not is_valid_operand(other):
            return NotImplemented

        return BitwiseAnd((other, self))

    # }}}

    # {{{ misc

    def __neg__(self) -> ArithmeticExpression:
        return -1*self

    def __pos__(self) -> ArithmeticExpression:
        return self

    def __call__(self, *args, **kwargs) -> Call | CallWithKwargs:
        if kwargs:
            from immutabledict import immutabledict
            return CallWithKwargs(self, args, immutabledict(kwargs))
        else:
            return Call(self, args)

    if not TYPE_CHECKING:
        # Subscript has an attribute 'index' which can't coexist with this.
        # Thus we're hiding this from mypy until it goes away.

        def index(self, subscript: ExpressionNode) -> ExpressionNode:
            """Return an expression representing ``self[subscript]``.

            .. versionadded:: 2014.3
            """

            warn("Expression.index(i) is deprecated and will be removed in 2H2025. "
                 "Use 'expr[i] 'instead.", DeprecationWarning, stacklevel=2)

            return self[subscript]

    def __getitem__(self, subscript: _Expression | EmptyOK) -> ExpressionNode:
        """Return an expression representing ``self[subscript]``. """

        if isinstance(subscript, EmptyOK):
            return Subscript(self, subscript.child)

        if subscript == ():
            warn("Expression.__getitem__ called with an empty tuple as an index. "
                 "This still returns just the aggregate (not a Subscript), "
                 "but this behavior will change in 2026. To avoid this warning "
                 "(and return a Subscript unconditionally), wrap the subscript "
                 "in pymbolic.primitives.EmptyOK.", DeprecationWarning, stacklevel=2)
            return self
        return Subscript(self, subscript)

    def attr(self, name: str) -> Lookup:
        """Return a :class:`Lookup` for *name* in *self*.
        """
        return Lookup(self, name)

    @property
    def a(self) -> _AttributeLookupCreator:
        """Provide a spelling ``expr.a.name`` for encoding attribute lookup.
        """
        return _AttributeLookupCreator(self)

    def __float__(self) -> float:
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

    def __str__(self) -> str:
        """Use the :meth:`make_stringifier` to return a human-readable
        string representation of *self*.
        """

        from pymbolic.mapper.stringifier import PREC_NONE
        return self.make_stringifier()(self, PREC_NONE)

    def _safe_repr(self, limit: int | None = None) -> str:
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

            elif isinstance(child, ExpressionNode):
                return child._safe_repr(limit=limit-1)
            else:
                return repr(child)

        from dataclasses import is_dataclass

        # NOTE: __getinitargs__() is deprecated, so skip it if possible
        if is_dataclass(self):
            initargs = tuple(getattr(self, fld.name) for fld in fields(self))
        else:
            initargs = self.__getinitargs__()
        initargs_str = ", ".join(strify_child(i, limit - 1) for i in initargs)

        return f"{self.__class__.__name__}({initargs_str})"

    def __repr__(self) -> str:
        return self._safe_repr()

    # }}}

    # {{{ hash/equality interface

    # This custom warning deduplication mechanism became necessary because the
    # sheer amount of warnings ended up leading to out-of-memory situations
    # with pytest which bufered all the warnings.
    _deprecation_warnings_issued: ClassVar[set[tuple[type[ExpressionNode], str]]] \
        = set()

    def __eq__(self, other) -> bool:
        """Provides equality testing with quick positive and negative paths
        based on :func:`id` and :meth:`__hash__`.
        """
        depr_key = (type(self), "__eq__")
        if depr_key not in self._deprecation_warnings_issued:
            warn(f"Expression.__eq__ is used by {self.__class__}. This is deprecated. "
                 "Use equality comparison supplied by expr_dataclass instead. "
                 "This will stop working in 2025.",
                 DeprecationWarning, stacklevel=2)
            self._deprecation_warnings_issued.add(depr_key)

        if self is other:
            return True
        elif hash(self) != hash(other):
            return False
        else:
            return self.is_equal(other)

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Provides caching for hash values.
        """
        depr_key = (type(self), "__hash__")
        if depr_key not in self._deprecation_warnings_issued:
            warn(f"Expression.__hash__ is used by {self.__class__}. "
                 "This is deprecated. "
                 "Use hash functions supplied by expr_dataclass instead. "
                 "This will stop working in 2025.",
                 DeprecationWarning, stacklevel=2)

            self._deprecation_warnings_issued.add(depr_key)

        try:
            return self._hash_value
        except AttributeError:
            self._hash_value: int = self.get_hash()
            return self._hash_value

    def __getstate__(self) -> tuple[Any]:
        return self.__getinitargs__()

    def __setstate__(self, state) -> None:
        # Can't use trivial pickling: _hash_value cache must stay unset
        assert len(self.init_arg_names) == len(state), type(self)
        for name, value in zip(self.init_arg_names, state, strict=True):
            object.__setattr__(self, name, value)

    # }}}

    # {{{ hash/equality backend

    def is_equal(self, other) -> bool:
        return (type(other) is type(self)
                and self.__getinitargs__() == other.__getinitargs__())

    def get_hash(self) -> int:
        return hash((type(self).__name__, *self.__getinitargs__()))

    # }}}

    # {{{ logical op constructors

    def not_(self) -> LogicalNot:
        """Return *self* wrapped in a :class:`LogicalNot`.

        .. versionadded:: 2015.2
        """
        return LogicalNot(self)

    def and_(self, other) -> LogicalAnd:
        """Return :class:`LogicalAnd` between *self* and *other*.

        .. versionadded:: 2015.2
        """
        return LogicalAnd((self, other))

    def or_(self, other) -> LogicalOr:
        """Return :class:`LogicalOr` between *self* and *other*.

        .. versionadded:: 2015.2
        """
        return LogicalOr((self, other))

    # }}}

    # {{{ comparison constructors

    def eq(self, other) -> Comparison:
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, "==", other)

    def ne(self, other) -> Comparison:
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, "!=", other)

    def le(self, other) -> Comparison:
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, "<=", other)

    def lt(self, other) -> Comparison:
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, "<", other)

    def ge(self, other) -> Comparison:
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, ">=", other)

    def gt(self, other) -> Comparison:
        """Return a :class:`Comparison` comparing *self* to *other*.

        .. versionadded:: 2015.2
        """
        return Comparison(self, ">", other)

    # }}}

    # {{{ prevent less / greater comparisons

    # /!\ Don't be tempted to resolve these to Comparison.

    def __le__(self, other) -> NoReturn:
        raise TypeError("expressions don't have an order")

    def __lt__(self, other) -> NoReturn:
        raise TypeError("expressions don't have an order")

    def __ge__(self, other) -> NoReturn:
        raise TypeError("expressions don't have an order")

    def __gt__(self, other) -> NoReturn:
        raise TypeError("expressions don't have an order")

    # }}}

    def __abs__(self) -> ExpressionNode:
        return Call(Variable("abs"), (self,))

    def __iter__(self):
        # prevent infinite loops (e.g. when inserting into numpy arrays)
        raise TypeError("expression types are not iterable")


# {{{ dataclasses support

# https://stackoverflow.com/a/1176023
_CAMEL_TO_SNAKE_RE = re.compile(
    r"""
        (?<=[a-z])      # preceded by lowercase
        (?=[A-Z])       # followed by uppercase
        |               #   OR
        (?<=[A-Z])      # preceded by lowercase
        (?=[A-Z][a-z])  # followed by uppercase, then lowercase
    """,
    re.X,
)


class _HasMapperMethod(Protocol):
    mapper_method: ClassVar[str]


def _augment_expression_dataclass(
            cls: type[DataclassInstance],
            *,
            generate_eq: bool,
            generate_hash: bool,
        ) -> None:
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
        """
        from warnings import warn
        from dataclasses import is_dataclass
        """
        + (f"""


        def {cls.__name__}_eq(self, other):
            if self is other:
                return True
            if self.__class__ is not other.__class__:
                return False
            if {generate_hash}:
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
        """ if generate_eq else "")
        + (f"""


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
        """ if generate_hash else "")
        + f"""


        def {cls.__name__}_init_arg_names(self):
            depr_key = (type(self), "init_arg_names")
            if depr_key not in self._deprecation_warnings_issued:
                warn("Attribute 'init_arg_names' of {cls} is deprecated and will "
                        "not have a default implementation starting from 2025. "
                        "Use 'dataclasses.fields' instead.",
                        DeprecationWarning, stacklevel=2)

                self._deprecation_warnings_issued.add(depr_key)

            return {fld_name_tuple}

        cls.init_arg_names = property({cls.__name__}_init_arg_names)


        def {cls.__name__}_getinitargs(self):
            depr_key = (type(self), "__getinitargs__")
            if depr_key not in self._deprecation_warnings_issued:
                warn("Method '__getinitargs__' of {cls} is deprecated and will "
                        "not have a default implementation starting from 2025. "
                        "Use 'dataclasses.fields' instead.",
                        DeprecationWarning, stacklevel=2)

                self._deprecation_warnings_issued.add(depr_key)

            return {attr_tuple}

        cls.__getinitargs__ = {cls.__name__}_getinitargs


        def {cls.__name__}_getstate(self):
            # We might get called on a non-dataclass subclass.
            if "_is_expr_dataclass" not in self.__class__.__dict__:
                from pymbolic.primitives import Expression
                return Expression.__getstate__(self)

            return {attr_tuple}

        cls.__getstate__ = {cls.__name__}_getstate


        def {cls.__name__}_setstate(self, state):
            # We might get called on a non-dataclass subclass.
            if "_is_expr_dataclass" not in self.__class__.__dict__:
                from pymbolic.primitives import Expression
                return Expression.__setstate__(self, state)

            for name, value in zip({fld_name_tuple}, state):
                object.__setattr__(self, name, value)

        cls.__setstate__ = {cls.__name__}_setstate
        """)

    exec_dict = {"cls": cls, "_MODULE_SOURCE_CODE": augment_code}
    exec(compile(augment_code,
                 f"<dataclass augmentation code for {cls}>", "exec"),
         exec_dict)

    # set a marker to detect classes whose subclasses may not be expr_dataclasses
    # type ignore because we don't want to announce the existence of this to the world.
    cls._is_expr_dataclass = True  # type: ignore[attr-defined]

    # {{{ assign mapper_method

    mm_cls = cast(type[_HasMapperMethod], cls)

    snake_clsname = _CAMEL_TO_SNAKE_RE.sub("_", mm_cls.__name__).lower()
    default_mapper_method_name = f"map_{snake_clsname}"

    # This covers two cases: the class does not have the attribute in the first
    # place, or it inherits a value but does not set it itself.
    sets_mapper_method = "mapper_method" in mm_cls.__dict__

    if sets_mapper_method:
        if default_mapper_method_name == mm_cls.mapper_method:
            warn(f"Explicit mapper_method on {mm_cls} not needed, default matches "
                 "explicit assignment. Just delete the explicit assignment.",
                 stacklevel=3)

    if not sets_mapper_method:
        mm_cls.mapper_method = intern(default_mapper_method_name)

    # }}}


_T = TypeVar("_T")


@dataclass_transform(frozen_default=True)
def expr_dataclass(
            init: bool = True,
            eq: bool = True,
            hash: bool = True,
        ) -> Callable[[type[_T]], type[_T]]:
    r"""A class decorator that makes the class a :func:`~dataclasses.dataclass`
    while also adding functionality needed for :class:`ExpressionNode`.
    Specifically, it adds cached hashing, equality comparisons
    with ``self is other`` shortcuts as well as some methods/attributes
    for backward compatibility (e.g. ``__getinitargs__``, ``init_arg_names``).

    It also adds a :attr:`ExpressionNode.mapper_method` based on the class name
    if not already present. If :attr:`~ExpressionNode.mapper_method` is inherited,
    it will be viewed as unset and replaced.

    Note that the class to which this decorator is applied need not be
    a subclass of :class:`ExpressionNode`.

    .. versionadded:: 2024.1
    """
    def map_cls(cls: type[_T]) -> type[_T]:
        # Frozen dataclasses (empirically) have a ~20% speed penalty in pymbolic,
        # and their frozen-ness is arguably a debug feature.

        # We provide __eq__/__hash__ below, don't redundantly generate it.
        dc_cls = dataclass(init=init, eq=False, frozen=__debug__, repr=False)(cls)

        # FIXME: I'm not sure how to tell mypy that dc_cls is type[DataclassInstance]
        # It should just understand that?
        _augment_expression_dataclass(
                  dc_cls,  # type: ignore[arg-type]
                  generate_eq=eq and "__eq__" not in cls.__dict__,
                  generate_hash=hash and "__hash__" not in cls.__dict__,
                  )
        return dc_cls

    return map_cls

# }}}


@expr_dataclass()
class AlgebraicLeaf(ExpressionNode):
    """An expression that serves as a leaf for arithmetic evaluation.
    This may end up having child nodes still, but they're not reached by
    ways of arithmetic."""
    pass


@expr_dataclass()
class Leaf(AlgebraicLeaf):
    """An expression that is irreducible, i.e. has no Expression-type parts
    whatsoever."""
    pass


@expr_dataclass()
class Variable(Leaf):
    """
    .. autoattribute:: name
    """
    name: str


@expr_dataclass()
class Wildcard(Leaf):
    """A general wildcard that can be used to substitute expressions."""


@expr_dataclass()
class DotWildcard(Leaf):
    """A wildcard that can be substituted for a single expression."""
    name: str


@expr_dataclass()
class StarWildcard(Leaf):
    """A wildcard that can be substituted by a sequence of expressions of
    non-negative length.
    """
    name: str


@expr_dataclass()
class FunctionSymbol(AlgebraicLeaf):
    """Represents the name of a function.

    May optionally have an `arg_count` attribute, which will
    allow `Call` to check the number of arguments.
    """


# {{{ structural primitives

@expr_dataclass()
class Call(AlgebraicLeaf):
    """A function invocation.

    .. autoattribute:: function
    .. autoattribute:: parameters
    """
    function: _Expression
    """Evaluates to the function to be called."""

    parameters: tuple[_Expression, ...]
    """
    A :class:`tuple` of positional parameters.
    """


@expr_dataclass()
class CallWithKwargs(AlgebraicLeaf):
    """A function invocation with keyword arguments.

    .. autoattribute:: function
    .. autoattribute:: parameters
    .. autoattribute:: kw_parameters
    """

    function: _Expression
    """Evaluates to the function to be called."""

    parameters: tuple[_Expression, ...]
    """A :class:`tuple` of positional parameters.
    """

    kw_parameters: Mapping[str, _Expression]
    """A dictionary mapping names to arguments.
    """

    def __post_init__(self):
        try:
            hash(self.kw_parameters)
        except Exception:
            warn("CallWithKwargs created with non-hashable kw_parameters. "
                 "This is deprecated and will stop working in 2025. "
                 "If you need an immutable mapping, "
                 "try the :mod:`immutabledict` package.",
                 DeprecationWarning, stacklevel=3
             )
            object.__setattr__(self, "kw_parameters", immutabledict(self.kw_parameters))


@expr_dataclass()
class Subscript(AlgebraicLeaf):
    """An array subscript."""

    aggregate: _Expression
    index: _Expression

    @property
    def index_tuple(self) -> tuple[_Expression, ...]:
        """
        Return :attr:`index` wrapped in a single-element tuple, if it is not already
        a tuple.
        """

        if isinstance(self.index, tuple):
            return self.index
        else:
            return (self.index,)


@expr_dataclass()
class Lookup(AlgebraicLeaf):
    """Access to an attribute of an *aggregate*, such as an attribute of a class."""

    aggregate: _Expression
    name: str

# }}}


# {{{ arithmetic primitives

@expr_dataclass()
class Sum(ExpressionNode):
    """
    .. autoattribute:: children

    .. automethod:: __add__
    .. automethod:: __radd__
    .. automethod:: __sub__
    .. automethod:: __bool__
    """

    children: tuple[_Expression, ...]

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


@expr_dataclass()
class Product(ExpressionNode):
    """
    .. autoattribute:: children

    .. automethod:: __mul__
    .. automethod:: __rmul__
    .. automethod:: __bool__
    """

    children: tuple[_Expression, ...]

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


@expr_dataclass()
class Min(ExpressionNode):
    """
    .. autoattribute:: children
    """
    children: tuple[_Expression, ...]


@expr_dataclass()
class Max(ExpressionNode):
    """
    .. autoattribute:: children
    """
    children: tuple[_Expression, ...]


@expr_dataclass()
class QuotientBase(ExpressionNode):
    numerator: ArithmeticExpression
    denominator: ArithmeticExpression

    @property
    def num(self):
        return self.numerator

    @property
    def den(self):
        return self.denominator

    def __bool__(self):
        return bool(self.numerator)

    __nonzero__ = __bool__


@expr_dataclass()
class Quotient(QuotientBase):
    """Bases: :class:`~pymbolic.ExpressionNode`

    .. autoattribute:: numerator
    .. autoattribute:: denominator
    """


@expr_dataclass()
class FloorDiv(QuotientBase):
    """Bases: :class:`~pymbolic.ExpressionNode`

    .. autoattribute:: numerator
    .. autoattribute:: denominator
    """


@expr_dataclass()
class Remainder(QuotientBase):
    """Bases: :class:`~pymbolic.ExpressionNode`

    .. autoattribute:: numerator
    .. autoattribute:: denominator
    """


@expr_dataclass()
class Power(ExpressionNode):
    """
    .. autoattribute:: base
    .. autoattribute:: exponent
    """

    base: ArithmeticExpression
    exponent: ArithmeticExpression

# }}}


# {{{ shift operators

@expr_dataclass()
class _ShiftOperator(ExpressionNode):
    shiftee: _Expression
    shift: _Expression


@expr_dataclass()
class LeftShift(_ShiftOperator):
    """Bases: :class:`~pymbolic.ExpressionNode`.

    .. autoattribute:: shiftee
    .. autoattribute:: shift
    """


@expr_dataclass()
class RightShift(_ShiftOperator):
    """Bases: :class:`~pymbolic.ExpressionNode`.

    .. autoattribute:: shiftee
    .. autoattribute:: shift
    """

# }}}


# {{{ bitwise operators

@expr_dataclass()
class BitwiseNot(ExpressionNode):
    """
    .. autoattribute:: child
    """

    child: _Expression


@expr_dataclass()
class BitwiseOr(ExpressionNode):
    """
    .. autoattribute:: children
    """

    children: tuple[_Expression, ...]


@expr_dataclass()
class BitwiseXor(ExpressionNode):
    """
    .. autoattribute:: children
    """
    children: tuple[_Expression, ...]


@expr_dataclass()
class BitwiseAnd(ExpressionNode):
    """
    .. autoattribute:: children
    """
    children: tuple[_Expression, ...]

# }}}


# {{{ comparisons, logic, conditionals

@expr_dataclass()
class Comparison(ExpressionNode):
    """
    .. autoattribute:: left
    .. autoattribute:: operator
    .. autoattribute:: right

    .. note::

        Unlike other expressions, comparisons are not implicitly constructed by
        comparing :class:`ExpressionNode` objects.
        See :meth:`pymbolic.ExpressionNode.eq` and related.

    .. autoattribute:: operator_to_name
    .. autoattribute:: name_to_operator
    """

    left: _Expression

    operator: str
    """One of ``[">", ">=", "==", "!=", "<", "<="]``."""

    right: _Expression

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


@expr_dataclass()
class LogicalNot(ExpressionNode):
    """
    .. autoattribute:: child
    """

    child: _Expression


@expr_dataclass()
class LogicalOr(ExpressionNode):
    """
    .. autoattribute:: children
    """

    children: tuple[_Expression, ...]


@expr_dataclass()
class LogicalAnd(ExpressionNode):
    """
    .. autoattribute:: children
    """
    children: tuple[_Expression, ...]


@expr_dataclass()
class If(ExpressionNode):
    """
    .. autoattribute:: condition
    .. autoattribute:: then
    .. autoattribute:: else_
    """

    condition: _Expression
    then: _Expression
    else_: _Expression

# }}}


# {{{ misc stuff

class cse_scope:  # noqa
    """Determines the lifetime for the saved value of a :class:`CommonSubexpression`.

    .. attribute:: EVALUATION
        :type: str

        The evaluated result lives for the duration of the evaluation of the
        current expression and is discarded thereafter.

    .. attribute:: EXPRESSION
        :type: str

        The evaluated result lives for the lifetime of the current expression
        (across multiple evaluations with multiple parameters) and is discarded
        when the expression is.

    .. attribute:: GLOBAL
        :type: str

        The evaluated result lives until the execution context dies.
    """

    EVALUATION = "pymbolic_eval"
    EXPRESSION = "pymbolic_expr"
    GLOBAL = "pymbolic_global"


@expr_dataclass()
class CommonSubexpression(ExpressionNode):
    """A helper for code generation and caching. Denotes a subexpression that
    should only be evaluated once. If, in code generation, it is assigned to
    a variable, a name starting with :attr:`prefix` should be used.

    .. autoattribute:: child
    .. autoattribute:: prefix
    .. autoattribute:: scope


    See :class:`pymbolic.mapper.c_code.CCodeMapper` for an example.
    """

    child: _Expression
    prefix: str | None = None
    scope: str = cse_scope.EVALUATION
    """
    One of the values in :class:`cse_scope`. See there for meaning.
    """

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


@expr_dataclass()
class Substitution(ExpressionNode):
    """Work-alike of :class:`~sympy.core.function.Subs`.

    .. autoattribute:: child
    .. autoattribute:: variables
    .. autoattribute:: values
    """

    child: _Expression
    variables: tuple[str, ...]
    values: tuple[_Expression, ...]


@expr_dataclass()
class Derivative(ExpressionNode):
    """Work-alike of sympy's :class:`~sympy.core.function.Derivative`.

    .. autoattribute:: child
    .. autoattribute:: variables
    """

    child: _Expression
    variables: tuple[str, ...]


SliceChildrenT: TypeAlias = (tuple[()]
        | tuple[_Expression | None]
        | tuple[_Expression | None, _Expression | None]
        | tuple[_Expression | None, _Expression | None, _Expression
            | None])


@expr_dataclass()
class Slice(ExpressionNode):
    """A slice expression as in a[1:7].

    .. autoattribute:: children

    .. autoproperty:: start
    .. autoproperty:: stop
    .. autoproperty:: step
    """

    children: SliceChildrenT

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


@expr_dataclass()
class NaN(AlgebraicLeaf):
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

    .. autoattribute:: data_type

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

def make_variable(var_or_string: Variable | str) -> Variable:
    if isinstance(var_or_string, str):
        return Variable(intern(var_or_string))
    else:
        return var_or_string


def subscript(expression, index):
    return Subscript(expression, index)


def flattened_sum(terms: Iterable[ArithmeticExpression]) -> ArithmeticExpression:
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
            ch = cast(tuple[ArithmeticExpression], item.children)
            queue.extend(ch)
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
                 for coefficient, expression
                 in zip(coefficients, expressions, strict=True)
                 if coefficient and expression)


def flattened_product(terms: Iterable[ArithmeticExpression]) -> ArithmeticExpression:
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
            ch = cast(tuple[ArithmeticExpression], item.children)
            queue.extend(ch)
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
VALID_CONSTANT_CLASSES: tuple[type, ...] = (int, float, complex)
_BOOL_CLASSES: tuple[type, ...] = (bool,)
VALID_OPERANDS = (ExpressionNode,)

try:
    import numpy
    VALID_CONSTANT_CLASSES += (numpy.number, numpy.bool_)
    _BOOL_CLASSES += (numpy.bool_, )
except ImportError:
    pass


def is_constant(value: object) -> TypeIs[Scalar]:
    return isinstance(value, VALID_CONSTANT_CLASSES)


def is_number(value: object) -> TypeIs[Number]:
    return (not isinstance(value, _BOOL_CLASSES)
        and isinstance(value, VALID_CONSTANT_CLASSES))


def is_valid_operand(value: object) -> TypeIs[_Expression]:
    return isinstance(value, VALID_OPERANDS) or is_constant(value)


def is_arithmetic_expression(value: object) -> TypeIs[ArithmeticExpression]:
    return not isinstance(value, _BOOL_CLASSES) and is_valid_operand(value)


def register_constant_class(class_):
    global VALID_CONSTANT_CLASSES

    VALID_CONSTANT_CLASSES += (class_,)


def unregister_constant_class(class_):
    global VALID_CONSTANT_CLASSES

    tmp = list(VALID_CONSTANT_CLASSES)
    tmp.remove(class_)
    VALID_CONSTANT_CLASSES = tuple(tmp)


def is_nonzero(value: object) -> bool:
    if value is None:
        raise ValueError("is_nonzero is undefined for None")

    try:
        return bool(value)
    except ValueError:
        return True


def is_zero(value: object) -> bool:
    return not is_nonzero(value)


def wrap_in_cse(expr: _Expression,
                prefix: str | None = None,
                scope: str | None = None) -> _Expression:
    warn("'wrap_in_cse' is deprecated and will be removed in 2025. Use "
         "'make_common_subexpression' with the `wrap_vars=False` flag instead.",
         DeprecationWarning, stacklevel=2)

    return make_common_subexpression(expr, prefix, scope, wrap_vars=False)


def make_common_subexpression(expr: _Expression,
                              prefix: str | None = None,
                              scope: str | None = None,
                              *,
                              wrap_vars: bool = True) -> _Expression:
    """Wrap *expr* in a :class:`CommonSubexpression` with *prefix*.

    If *expr* is a :mod:`numpy` object array, each individual entry is instead
    wrapped. If *expr* is a :class:`pymbolic.geometric_algebra.MultiVector`, each
    coefficient is individually wrapped. In general, the function tries to avoid
    re-wrapping existing :class:`CommonSubexpression` if the same scope is given.

    See :class:`CommonSubexpression` for the meaning of *prefix* and *scope*. The
    scope defaults to :attr:`cse_scope.EVALUATION`.

    :arg wrap_vars: If *True*, this also wraps a :class:`~pymbolic.primitives.Variable`
        and its subscripts. Otherwise, these expressions are returned as is.
    """

    if is_constant(expr):
        return expr

    if not wrap_vars and isinstance(expr, Variable | Subscript):
        return expr

    # handle CSE re-wrapping
    if scope is None:
        scope = cse_scope.EVALUATION

    if isinstance(expr, CommonSubexpression):
        if scope == cse_scope.EVALUATION or expr.scope == scope:
            return expr

    # handle MultiVector
    from pymbolic.geometric_algebra import MultiVector

    if isinstance(expr, MultiVector):
        new_data = {}
        for bits, coeff in expr.data.items():
            if prefix is not None:
                blade_str = expr.space.blade_bits_to_str(bits, "")
                component_prefix = f"{prefix}_{blade_str}"
            else:
                component_prefix = None

            new_data[bits] = make_common_subexpression(
                    coeff, component_prefix, scope, wrap_vars=wrap_vars)

        return MultiVector(new_data, expr.space)

    # handle numpy object arrays
    try:
        import numpy as np

        if isinstance(expr, np.ndarray) and expr.dtype.char == "O":
            is_obj_array = True
            logical_shape = expr.shape
        else:
            is_obj_array = False
            logical_shape = ()
    except ImportError:
        is_obj_array = False
        logical_shape = ()

    if is_obj_array and logical_shape != ():
        assert isinstance(expr, np.ndarray)

        result = np.zeros(logical_shape, dtype=object)
        for i in np.ndindex(logical_shape):
            if prefix is not None:
                bits = "_".join(str(i_i) for i_i in i)
                component_prefix = f"{prefix}_{bits}"
            else:
                component_prefix = None

            result[i] = make_common_subexpression(
                    expr[i], component_prefix, scope, wrap_vars=wrap_vars)

        return result

    # everything else gets re-wrapped
    return CommonSubexpression(expr, prefix, scope)


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
    return flat_obj_array(*[vfld[i] for i in components])


def make_sym_array(name, shape, var_factory=Variable):
    vfld = var_factory(name)
    if shape == ():
        return vfld

    import numpy as np
    result = np.zeros(shape, dtype=object)
    for i in np.ndindex(shape):
        result[i] = vfld[i]

    return result


def variables(s):
    """Return a list of variables for each (space-delimited) identifier
    in *s*.
    """
    return [Variable(s_i) for s_i in s.split() if s_i]

# }}}


__getattr__ = partial(module_getattr_for_deprecations, __name__, {
        "Expression": ("ExpressionNode", ExpressionNode, 2026),
        })


# vim: foldmethod=marker
