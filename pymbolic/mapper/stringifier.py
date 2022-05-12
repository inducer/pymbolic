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

from pymbolic.mapper import Mapper, CachedMapper
import pymbolic.primitives as p

__doc__ = """
.. _prec-constants:

Precedence constants
********************

.. data:: PREC_CALL
.. data:: PREC_POWER
.. data:: PREC_UNARY
.. data:: PREC_PRODUCT
.. data:: PREC_SUM
.. data:: PREC_SHIFT
.. data:: PREC_BITWISE_AND
.. data:: PREC_BITWISE_XOR
.. data:: PREC_BITWISE_OR
.. data:: PREC_COMPARISON
.. data:: PREC_LOGICAL_AND
.. data:: PREC_LOGICAL_OR
.. data:: PREC_IF
.. data:: PREC_NONE

Mappers
*******

.. autoclass:: StringifyMapper

    .. automethod:: __call__

.. autoclass:: CSESplittingStringifyMapperMixin

.. autoclass:: LaTeXMapper
"""


PREC_CALL = 15
PREC_POWER = 14
PREC_UNARY = 13
PREC_PRODUCT = 12
PREC_SUM = 11
PREC_SHIFT = 10
PREC_BITWISE_AND = 9
PREC_BITWISE_XOR = 8
PREC_BITWISE_OR = 7
PREC_COMPARISON = 6
PREC_LOGICAL_AND = 5
PREC_LOGICAL_OR = 4
PREC_IF = 3
PREC_NONE = 0


# {{{ stringifier

class StringifyMapper(Mapper):
    """A mapper to turn an expression tree into a string.

    :class:`pymbolic.primitives.Expression.__str__` is often implemented using
    this mapper.

    When it encounters an unsupported :class:`pymbolic.primitives.Expression`
    subclass, it calls its :meth:`pymbolic.primitives.Expression.make_stringifier`
    method to get a :class:`StringifyMapper` that potentially does.
    """

    # {{{ replaceable string composition interface

    def format(self, s, *args):
        return s % args

    def join(self, joiner, iterable):
        return self.format(joiner.join("%s" for _ in iterable), *iterable)

    def rec_with_force_parens_around(self, expr, *args, **kwargs):
        force_parens_around = kwargs.pop("force_parens_around", ())

        result = self.rec(expr, *args, **kwargs)

        if isinstance(expr, force_parens_around):
            result = f"({result})"

        return result

    def join_rec(self, joiner, iterable, prec, *args, **kwargs):
        f = joiner.join("%s" for _ in iterable)
        return self.format(f,
                *[self.rec_with_force_parens_around(i, prec, *args, **kwargs)
                    for i in iterable])

    def parenthesize(self, s):
        return f"({s})"

    def parenthesize_if_needed(self, s, enclosing_prec, my_prec):
        if enclosing_prec > my_prec:
            return f"({s})"
        else:
            return s

    # }}}

    # {{{ mappings

    def handle_unsupported_expression(self, expr, enclosing_prec, *args, **kwargs):
        strifier = expr.make_stringifier(self)
        if isinstance(self, type(strifier)):
            raise ValueError(
                    f"stringifier '{self}' can't handle '{expr.__class__}'")
        return strifier(
                expr, enclosing_prec, *args, **kwargs)

    def map_constant(self, expr, enclosing_prec, *args, **kwargs):
        result = str(expr)

        if not (result.startswith("(") and result.endswith(")")) \
                and ("-" in result or "+" in result) \
                and (enclosing_prec > PREC_SUM):
            return self.parenthesize(result)
        else:
            return result

    def map_variable(self, expr, enclosing_prec, *args, **kwargs):
        return expr.name

    def map_wildcard(self, expr, enclosing_prec, *args, **kwargs):
        return "*"

    def map_function_symbol(self, expr, enclosing_prec, *args, **kwargs):
        return expr.__class__.__name__

    def map_call(self, expr, enclosing_prec, *args, **kwargs):
        return self.format("%s(%s)",
                self.rec(expr.function, PREC_CALL, *args, **kwargs),
                self.join_rec(", ", expr.parameters, PREC_NONE, *args, **kwargs))

    def map_call_with_kwargs(self, expr, enclosing_prec, *args, **kwargs):
        args_strings = (
                tuple([
                    self.rec(ch, PREC_NONE, *args, **kwargs)
                    for ch in expr.parameters
                    ])
                +  # noqa: W504
                tuple([
                    "{}={}".format(name, self.rec(ch, PREC_NONE, *args, **kwargs))
                    for name, ch in expr.kw_parameters.items()
                    ])
                )
        return self.format("%s(%s)",
                self.rec(expr.function, PREC_CALL, *args, **kwargs),
                ", ".join(args_strings))

    def map_subscript(self, expr, enclosing_prec, *args, **kwargs):
        if isinstance(expr.index, tuple):
            index_str = self.join_rec(", ", expr.index, PREC_NONE, *args, **kwargs)
        else:
            index_str = self.rec(expr.index, PREC_NONE, *args, **kwargs)

        return self.parenthesize_if_needed(
                self.format("%s[%s]",
                    self.rec(expr.aggregate, PREC_CALL, *args, **kwargs),
                    index_str),
                enclosing_prec, PREC_CALL)

    def map_lookup(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.format("%s.%s",
                    self.rec(expr.aggregate, PREC_CALL, *args, **kwargs),
                    expr.name),
                enclosing_prec, PREC_CALL)

    def map_sum(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(" + ", expr.children, PREC_SUM, *args, **kwargs),
                enclosing_prec, PREC_SUM)

    # {{{ multiplicative operators

    multiplicative_primitives = (p.Product, p.Quotient, p.FloorDiv, p.Remainder)

    def map_product(self, expr, enclosing_prec, *args, **kwargs):
        kwargs["force_parens_around"] = (p.Quotient, p.FloorDiv, p.Remainder)
        return self.parenthesize_if_needed(
                self.join_rec("*", expr.children, PREC_PRODUCT, *args, **kwargs),
                enclosing_prec, PREC_PRODUCT)

    def map_quotient(self, expr, enclosing_prec, *args, **kwargs):
        kwargs["force_parens_around"] = self.multiplicative_primitives
        return self.parenthesize_if_needed(
                self.format("%s / %s",
                    # space is necessary--otherwise '/*' becomes
                    # start-of-comment in C. ('*' from dereference)
                    self.rec_with_force_parens_around(expr.numerator, PREC_PRODUCT,
                        *args, **kwargs),
                    self.rec_with_force_parens_around(
                        expr.denominator, PREC_PRODUCT, *args, **kwargs)),
                enclosing_prec, PREC_PRODUCT)

    def map_floor_div(self, expr, enclosing_prec, *args, **kwargs):
        kwargs["force_parens_around"] = self.multiplicative_primitives
        return self.parenthesize_if_needed(
                self.format("%s // %s",
                    self.rec_with_force_parens_around(
                        expr.numerator, PREC_PRODUCT, *args, **kwargs),
                    self.rec_with_force_parens_around(
                        expr.denominator, PREC_PRODUCT, *args, **kwargs)),
                enclosing_prec, PREC_PRODUCT)

    def map_remainder(self, expr, enclosing_prec, *args, **kwargs):
        kwargs["force_parens_around"] = self.multiplicative_primitives
        return self.parenthesize_if_needed(
                self.format("%s %% %s",
                    self.rec_with_force_parens_around(
                        expr.numerator, PREC_PRODUCT, *args, **kwargs),
                    self.rec_with_force_parens_around(
                        expr.denominator, PREC_PRODUCT, *args, **kwargs)),
                enclosing_prec, PREC_PRODUCT)

    # }}}

    def map_power(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.format("%s**%s",
                    self.rec(expr.base, PREC_POWER, *args, **kwargs),
                    self.rec(expr.exponent, PREC_POWER, *args, **kwargs)),
                enclosing_prec, PREC_POWER)

    def map_polynomial(self, expr, enclosing_prec, *args, **kwargs):
        from pymbolic.primitives import flattened_sum
        return self.rec(flattened_sum(
            [coeff*expr.base**exp for exp, coeff in expr.data[::-1]]),
            enclosing_prec, *args, **kwargs)

    def map_left_shift(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                # +1 to address
                # https://gitlab.tiker.net/inducer/pymbolic/issues/6
                self.format("%s << %s",
                    self.rec(expr.shiftee, PREC_SHIFT+1, *args, **kwargs),
                    self.rec(expr.shift, PREC_SHIFT+1, *args, **kwargs)),
                enclosing_prec, PREC_SHIFT)

    def map_right_shift(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                # +1 to address
                # https://gitlab.tiker.net/inducer/pymbolic/issues/6
                self.format("%s >> %s",
                    self.rec(expr.shiftee, PREC_SHIFT+1, *args, **kwargs),
                    self.rec(expr.shift, PREC_SHIFT+1, *args, **kwargs)),
                enclosing_prec, PREC_SHIFT)

    def map_bitwise_not(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                "~" + self.rec(expr.child, PREC_UNARY, *args, **kwargs),
                enclosing_prec, PREC_UNARY)

    def map_bitwise_or(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(
                    " | ", expr.children, PREC_BITWISE_OR, *args, **kwargs),
                enclosing_prec, PREC_BITWISE_OR)

    def map_bitwise_xor(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(
                    " ^ ", expr.children, PREC_BITWISE_XOR, *args, **kwargs),
                enclosing_prec, PREC_BITWISE_XOR)

    def map_bitwise_and(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(
                    " & ", expr.children, PREC_BITWISE_AND, *args, **kwargs),
                enclosing_prec, PREC_BITWISE_AND)

    def map_comparison(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.format("%s %s %s",
                    self.rec(expr.left, PREC_COMPARISON, *args, **kwargs),
                    expr.operator,
                    self.rec(expr.right, PREC_COMPARISON, *args, **kwargs)),
                enclosing_prec, PREC_COMPARISON)

    def map_logical_not(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                "not " + self.rec(expr.child, PREC_UNARY, *args, **kwargs),
                enclosing_prec, PREC_UNARY)

    def map_logical_or(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(
                    " or ", expr.children, PREC_LOGICAL_OR, *args, **kwargs),
                enclosing_prec, PREC_LOGICAL_OR)

    def map_logical_and(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(
                    " and ", expr.children, PREC_LOGICAL_AND, *args, **kwargs),
                enclosing_prec, PREC_LOGICAL_AND)

    def map_list(self, expr, enclosing_prec, *args, **kwargs):
        return self.format(
                "[%s]", self.join_rec(", ", expr, PREC_NONE, *args, **kwargs))

    map_vector = map_list

    def map_tuple(self, expr, enclosing_prec, *args, **kwargs):
        el_str = ", ".join(
                self.rec(child, PREC_NONE, *args, **kwargs) for child in expr)
        if len(expr) == 1:
            el_str += ","

        return f"({el_str})"

    def map_numpy_array(self, expr, enclosing_prec, *args, **kwargs):
        import numpy

        str_array = numpy.zeros(expr.shape, dtype="object")
        max_length = 0
        for i in numpy.ndindex(expr.shape):
            s = self.rec(expr[i], PREC_NONE, *args, **kwargs)
            max_length = max(len(s), max_length)
            str_array[i] = s.replace("\n", "\n  ")

        if len(expr.shape) == 1 and max_length < 15:
            return "array({})".format(", ".join(str_array))
        else:
            lines = ["  {}: {}\n".format(
                ",".join(str(i_i) for i_i in i), val)
                for i, val in numpy.ndenumerate(str_array)]
            if max_length > 70:
                splitter = "  " + "-"*75 + "\n"
                return "array(\n{})".format(splitter.join(lines))
            else:
                return "array(\n{})".format("".join(lines))

    def map_multivector(self, expr, enclosing_prec, *args, **kwargs):
        return expr.stringify(self.rec, enclosing_prec, *args, **kwargs)

    def map_common_subexpression(self, expr, enclosing_prec, *args, **kwargs):
        from pymbolic.primitives import CommonSubexpression
        if type(expr) is CommonSubexpression:
            type_name = "CSE"
        else:
            type_name = type(expr).__name__

        return self.format("%s(%s)",
                type_name, self.rec(expr.child, PREC_NONE, *args, **kwargs))

    def map_if(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                "{} if {} else {}".format(
                    self.rec(expr.then, PREC_LOGICAL_OR, *args, **kwargs),
                    self.rec(expr.condition, PREC_LOGICAL_OR, *args, **kwargs),
                    self.rec(expr.else_, PREC_LOGICAL_OR, *args, **kwargs)),
                enclosing_prec, PREC_IF)

    def map_if_positive(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                "{} if {} > 0 else {}".format(
                    self.rec(expr.then, PREC_LOGICAL_OR, *args, **kwargs),
                    self.rec(expr.criterion, PREC_LOGICAL_OR, *args, **kwargs),
                    self.rec(expr.else_, PREC_LOGICAL_OR, *args, **kwargs)),
                enclosing_prec, PREC_IF)

    def map_min(self, expr, enclosing_prec, *args, **kwargs):
        what = type(expr).__name__.lower()
        return self.format("%s(%s)",
                what, self.join_rec(", ", expr.children, PREC_NONE, *args, **kwargs))

    map_max = map_min

    def map_derivative(self, expr, enclosing_prec, *args, **kwargs):
        derivs = " ".join(f"d/d{v}" for v in expr.variables)

        return "{} {}".format(
                derivs,
                self.rec(expr.child, PREC_PRODUCT, *args, **kwargs))

    def map_substitution(self, expr, enclosing_prec, *args, **kwargs):
        substs = ", ".join(
                "{}={}".format(name, self.rec(val, PREC_NONE, *args, **kwargs))
                for name, val in zip(expr.variables, expr.values))

        return "[%s]{%s}" % (
                self.rec(expr.child, PREC_NONE, *args, **kwargs),
                substs)

    def map_slice(self, expr, enclosing_prec, *args, **kwargs):
        children = []
        for child in expr.children:
            if child is None:
                children.append("")
            else:
                children.append(self.rec(child, PREC_NONE, *args, **kwargs))

        return self.parenthesize_if_needed(
                self.join(":", children),
                enclosing_prec, PREC_NONE)

    def map_nan(self, expr, enclosing_prec, *args, **kwargs):
        return "NaN"

    # }}}

    def __call__(self, expr, prec=PREC_NONE, *args, **kwargs):
        """Return a string corresponding to *expr*. If the enclosing
        precedence level *prec* is higher than *prec* (see :ref:`prec-constants`),
        parenthesize the result.
        """

        return Mapper.__call__(self, expr, prec, *args, **kwargs)


class CachedStringifyMapper(StringifyMapper, CachedMapper):
    def __init__(self) -> None:
        StringifyMapper.__init__(self)
        CachedMapper.__init__(self)

    def __call__(self, expr, prec=PREC_NONE, *args, **kwargs):
        return CachedMapper.__call__(expr, prec, *args, **kwargs)

# }}}


# {{{ cse-splitting stringifier

class CSESplittingStringifyMapperMixin:
    """A :term:`mix-in` for subclasses of
    :class:`StringifyMapper` that collects
    "variable assignments" for
    :class:`pymbolic.primitives.CommonSubexpression` objects.

    .. attribute:: cse_to_name

        A :class:`dict` mapping expressions to CSE variable names.

    .. attribute:: cse_names

        A :class:`set` of names already assigned.

    .. attribute:: cse_name_list

        A :class:`list` of tuples of names and their string representations,
        in order of their dependencies. When generating code, walk down these names
        in order, and the generated code will never reference
        an undefined variable.

    See :class:`pymbolic.mapper.c_code.CCodeMapper` for an example
    of the use of this mix-in.
    """
    def __init__(self):
        self.cse_to_name = {}
        self.cse_names = set()
        self.cse_name_list = []

        super().__init__()

    def map_common_subexpression(self, expr, enclosing_prec, *args, **kwargs):
        # This is here for compatibility, in case the constructor did not get called.
        try:
            self.cse_to_name
        except AttributeError:
            from warnings import warn
            warn("Constructor of CSESplittingStringifyMapperMixin did not get "
                    "called. This is deprecated and will stop working in 2022.",
                    DeprecationWarning)

            self.cse_to_name = {}
            self.cse_names = set()
            self.cse_name_list = []

        try:
            cse_name = self.cse_to_name[expr.child]
        except KeyError:
            str_child = self.rec(expr.child, PREC_NONE, *args, **kwargs)

            if expr.prefix is not None:
                def generate_cse_names():
                    yield expr.prefix
                    i = 2
                    while True:
                        yield expr.prefix + f"_{i}"
                        i += 1
            else:
                def generate_cse_names():
                    i = 0
                    while True:
                        yield "CSE"+str(i)
                        i += 1

            for cse_name in generate_cse_names():
                if cse_name not in self.cse_names:
                    break

            self.cse_name_list.append((cse_name, str_child))
            self.cse_to_name[expr.child] = cse_name
            self.cse_names.add(cse_name)

        return cse_name

    def get_cse_strings(self):
        return [f"{cse_name} : {cse_str}"
                for cse_name, cse_str in
                    sorted(getattr(self, "cse_name_list", []))]

# }}}


# {{{ sorting stringifier

class SortingStringifyMapper(StringifyMapper):
    def __init__(self, reverse=True):
        super().__init__()
        self.reverse = reverse

    def map_sum(self, expr, enclosing_prec, *args, **kwargs):
        entries = [self.rec(i, PREC_SUM, *args, **kwargs) for i in expr.children]
        entries.sort(reverse=self.reverse)
        return self.parenthesize_if_needed(
                self.join(" + ", entries),
                enclosing_prec, PREC_SUM)

    def map_product(self, expr, enclosing_prec, *args, **kwargs):
        entries = [self.rec(i, PREC_PRODUCT, *args, **kwargs) for i in expr.children]
        entries.sort(reverse=self.reverse)
        return self.parenthesize_if_needed(
                self.join("*", entries),
                enclosing_prec, PREC_PRODUCT)

# }}}


# {{{ simplifying, sorting stringifier

class SimplifyingSortingStringifyMapper(StringifyMapper):
    def __init__(self, reverse=True):
        super().__init__()
        self.reverse = reverse

    def map_sum(self, expr, enclosing_prec, *args, **kwargs):
        def get_neg_product(expr):
            from pymbolic.primitives import is_zero, Product

            if isinstance(expr, Product) \
                    and len(expr.children) and is_zero(expr.children[0]+1):
                if len(expr.children) == 2:
                    # only the minus sign and the other child
                    return expr.children[1]
                else:
                    return Product(expr.children[1:])
            else:
                return None

        positives = []
        negatives = []

        for ch in expr.children:
            neg_prod = get_neg_product(ch)
            if neg_prod is not None:
                negatives.append(self.rec(neg_prod, PREC_PRODUCT, *args, **kwargs))
            else:
                positives.append(self.rec(ch, PREC_SUM, *args, **kwargs))

        positives.sort(reverse=self.reverse)
        positives = " + ".join(positives)
        negatives.sort(reverse=self.reverse)
        negatives = self.join("",
                [self.format(" - %s", entry) for entry in negatives])

        result = positives + negatives

        return self.parenthesize_if_needed(result, enclosing_prec, PREC_SUM)

    def map_product(self, expr, enclosing_prec, *args, **kwargs):
        entries = []
        i = 0
        from pymbolic.primitives import is_zero

        while i < len(expr.children):
            child = expr.children[i]
            if False and is_zero(child+1) and i+1 < len(expr.children):
                # NOTE: That space needs to be there.
                # Otherwise two unary minus signs merge into a pre-decrement.
                entries.append(
                        self.format(
                            "- %s", self.rec(
                                expr.children[i+1], PREC_UNARY, *args, **kwargs)))
                i += 2
            else:
                entries.append(self.rec(child, PREC_PRODUCT, *args, **kwargs))
                i += 1

        entries.sort(reverse=self.reverse)
        result = "*".join(entries)

        return self.parenthesize_if_needed(result, enclosing_prec, PREC_PRODUCT)

# }}}


# {{{ latex stringifier

class LaTeXMapper(StringifyMapper):

    COMPARISON_OP_TO_LATEX = {
        "==": r"=",
        "!=": r"\ne",
        "<=": r"\le",
        ">=": r"\ge",
        "<":  r"<",
        ">":  r">",
        }

    def map_remainder(self, expr, enclosing_prec, *args, **kwargs):
        return self.format(r"(%s \bmod %s)",
                self.rec(expr.numerator, PREC_PRODUCT, *args, **kwargs),
                self.rec(expr.denominator, PREC_POWER, *args, **kwargs)),

    def map_left_shift(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.format(r"%s \ll %s",
                    self.rec(expr.shiftee, PREC_SHIFT+1, *args, **kwargs),
                    self.rec(expr.shift, PREC_SHIFT+1, *args, **kwargs)),
                enclosing_prec, PREC_SHIFT)

    def map_right_shift(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.format(r"%s \gg %s",
                    self.rec(expr.shiftee, PREC_SHIFT+1, *args, **kwargs),
                    self.rec(expr.shift, PREC_SHIFT+1, *args, **kwargs)),
                enclosing_prec, PREC_SHIFT)

    def map_bitwise_xor(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(
                    r" \wedge ", expr.children, PREC_BITWISE_XOR, *args, **kwargs),
                enclosing_prec, PREC_BITWISE_XOR)

    def map_product(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(" ", expr.children, PREC_PRODUCT, *args, **kwargs),
                enclosing_prec, PREC_PRODUCT)

    def map_power(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.format("{%s}^{%s}",
                    self.rec(expr.base, PREC_NONE, *args, **kwargs),
                    self.rec(expr.exponent, PREC_NONE, *args, **kwargs)),
                enclosing_prec, PREC_NONE)

    def map_min(self, expr, enclosing_prec, *args, **kwargs):
        from pytools import is_single_valued
        if is_single_valued(expr.children):
            return self.rec(expr.children[0], enclosing_prec)

        what = type(expr).__name__.lower()
        return self.format(r"\%s(%s)",
                what, self.join_rec(", ", expr.children, PREC_NONE, *args, **kwargs))

    def map_max(self, expr, enclosing_prec):
        return self.map_min(expr, enclosing_prec)

    def map_floor_div(self, expr, enclosing_prec, *args, **kwargs):
        return self.format(r"\lfloor {%s} / {%s} \rfloor",
                    self.rec(expr.numerator, PREC_NONE, *args, **kwargs),
                    self.rec(expr.denominator, PREC_NONE, *args, **kwargs))

    def map_subscript(self, expr, enclosing_prec, *args, **kwargs):
        if isinstance(expr.index, tuple):
            index_str = self.join_rec(", ", expr.index, PREC_NONE, *args, **kwargs)
        else:
            index_str = self.rec(expr.index, PREC_NONE, *args, **kwargs)

        return self.format("{%s}_{%s}",
                    self.rec(expr.aggregate, PREC_CALL, *args, **kwargs),
                    index_str)

    def map_logical_not(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                r"\neg " + self.rec(expr.child, PREC_UNARY, *args, **kwargs),
                enclosing_prec, PREC_UNARY)

    def map_logical_or(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(
                    r" \vee ", expr.children, PREC_LOGICAL_OR, *args, **kwargs),
                enclosing_prec, PREC_LOGICAL_OR)

    def map_logical_and(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.join_rec(
                    r" \wedge ", expr.children, PREC_LOGICAL_AND, *args, **kwargs),
                enclosing_prec, PREC_LOGICAL_AND)

    def map_comparison(self, expr, enclosing_prec, *args, **kwargs):
        return self.parenthesize_if_needed(
                self.format("%s %s %s",
                    self.rec(expr.left, PREC_COMPARISON, *args, **kwargs),
                    self.COMPARISON_OP_TO_LATEX[expr.operator],
                    self.rec(expr.right, PREC_COMPARISON, *args, **kwargs)),
                enclosing_prec, PREC_COMPARISON)

    def map_substitution(self, expr, enclosing_prec, *args, **kwargs):
        substs = ", ".join(
                "{}={}".format(name, self.rec(val, PREC_NONE, *args, **kwargs))
                for name, val in zip(expr.variables, expr.values))

        return self.format(r"[%s]\{%s\}",
                self.rec(expr.child, PREC_NONE, *args, **kwargs),
                substs)

    def map_derivative(self, expr, enclosing_prec, *args, **kwargs):
        derivs = " ".join(
                r"\frac{\partial}{\partial %s}" % v
                for v in expr.variables)

        return self.format("%s %s",
                derivs, self.rec(expr.child, PREC_PRODUCT, *args, **kwargs))

# }}}

# vim: fdm=marker
