"""
.. autoclass:: CCodeMapper
"""
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

from typing import TYPE_CHECKING

from typing_extensions import override

import pymbolic.primitives as p
from pymbolic.mapper.stringifier import (
    PREC_CALL,
    PREC_LOGICAL_AND,
    PREC_LOGICAL_OR,
    PREC_NONE,
    PREC_UNARY,
    SimplifyingSortingStringifyMapper,
)


if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from pymbolic.typing import Expression


class CCodeMapper(SimplifyingSortingStringifyMapper[[]]):
    """Generate C code for expressions, while extracting
    :class:`pymbolic.primitives.CommonSubexpression` instances.

    As an example, define a fairly simple expression *expr*:

    .. doctest::

        >>> import pymbolic.primitives as p
        >>> CSE = p.make_common_subexpression
        >>> x = p.Variable("x")
        >>> u = CSE(3*x**2-5, "u")
        >>> expr = u/(u+3)*(u+5)
        >>> print(expr)
        (CSE(3*x**2 + -5) / (CSE(3*x**2 + -5) + 3))*(CSE(3*x**2 + -5) + 5)

    Notice that if we were to directly generate this code without the added
    `CSE`, the subexpression *u* would be evaluated multiple times. Wrapping the
    expression as above avoids this unnecessary cost.

    .. doctest::

        >>> from pymbolic.mapper.c_code import CCodeMapper as CCM
        >>> ccm = CCM()
        >>> result = ccm(expr)

        >>> for name, value in ccm.cse_name_list:
        ...     print("%s = %s;" % (name, value))
        ...
        _cse_u = 3 * x * x + -5;
        >>> print(result)
        _cse_u / (_cse_u + 3) * (_cse_u + 5)

    See :class:`pymbolic.mapper.stringifier.CSESplittingStringifyMapperMixin`
    for the ``cse_*`` attributes.
    """

    cse_prefix: str
    cse_to_name: dict[Expression, str]
    cse_names: set[str]
    cse_name_list: list[tuple[str, str]]
    complex_constant_base_type: str

    def __init__(self,
                 reverse: bool = True,
                 cse_prefix: str = "_cse",
                 complex_constant_base_type: str = "double",
                 cse_name_list: Sequence[tuple[str, str]] | None = None) -> None:
        if cse_name_list is None:
            cse_name_list = []

        super().__init__(reverse)
        self.cse_prefix = cse_prefix

        self.cse_to_name = {cse: name for name, cse in cse_name_list}
        self.cse_names = {cse for _name, cse in cse_name_list}
        self.cse_name_list = list(cse_name_list)

        self.complex_constant_base_type = complex_constant_base_type

    def copy(self,
             cse_name_list: Sequence[tuple[str, str]] | None = None,
        ) -> CCodeMapper:
        if cse_name_list is None:
            cse_name_list = self.cse_name_list

        return CCodeMapper(self.reverse,
                self.cse_prefix, self.complex_constant_base_type,
                cse_name_list)

    def copy_with_mapped_cses(
            self, cses_and_values: Sequence[tuple[str, str]]) -> CCodeMapper:
        return self.copy((*self.cse_name_list, *cses_and_values))

    # {{{ mappings

    @override
    def map_product(self, expr: p.Product, /, enclosing_prec: int) -> str:
        from pymbolic.mapper.stringifier import PREC_PRODUCT
        return self.parenthesize_if_needed(
                # Spaces prevent '**z' (times dereference z), which
                # is hard to read.

                self.join_rec(" * ", expr.children, PREC_PRODUCT),
                enclosing_prec, PREC_PRODUCT)

    @override
    def map_constant(self, x: object, /, enclosing_prec: int) -> str:
        if isinstance(x, complex):
            base = self.complex_constant_base_type
            real = self.map_constant(x.real, PREC_NONE)
            imag = self.map_constant(x.imag, PREC_NONE)

            # NOTE: this will need the <complex.h> include to work
            # FIXME: MSVC does not support <complex.h>, so this will not work.
            # (AFAIK, it uses a struct instead and does not support arithmetic)
            return f"({base} complex)({real} + {imag} * _Imaginary_I)"
        else:
            return super().map_constant(x, enclosing_prec)

    @override
    def map_call(self, expr: p.Call, /, enclosing_prec: int) -> str:
        if isinstance(expr.function, p.Variable):
            func = expr.function.name
        else:
            func = self.rec(expr.function, PREC_CALL)

        return self.format("%s(%s)",
                func,
                self.join_rec(", ", expr.parameters, PREC_NONE))

    @override
    def map_power(self, expr: p.Power, /, enclosing_prec: int) -> str:
        from pymbolic.mapper.stringifier import PREC_NONE
        from pymbolic.primitives import is_constant, is_zero
        if is_constant(expr.exponent):
            if is_zero(expr.exponent):
                return "1"
            elif is_zero(expr.exponent - 1):
                return self.rec(expr.base, enclosing_prec)
            elif is_zero(expr.exponent - 2):
                return self.rec(expr.base*expr.base, enclosing_prec)

        return self.format("pow(%s, %s)",
                self.rec(expr.base, PREC_NONE),
                self.rec(expr.exponent, PREC_NONE))

    @override
    def map_floor_div(self, expr: p.FloorDiv, /, enclosing_prec: int) -> str:
        # Let's see how bad of an idea this is--sane people would only
        # apply this to integers, right?

        from pymbolic.mapper.stringifier import PREC_POWER, PREC_PRODUCT
        return self.format("(%s/%s)",
                    self.rec(expr.numerator, PREC_PRODUCT),
                    self.rec(expr.denominator, PREC_POWER))  # analogous to ^{-1}

    @override
    def map_logical_not(self, expr: p.LogicalNot, /, enclosing_prec: int) -> str:
        child = self.rec(expr.child, PREC_UNARY)
        return self.parenthesize_if_needed(f"!{child}", enclosing_prec, PREC_UNARY)

    @override
    def map_logical_and(self, expr: p.LogicalAnd, /, enclosing_prec: int) -> str:
        return self.parenthesize_if_needed(
                self.join_rec(" && ", expr.children, PREC_LOGICAL_AND),
                enclosing_prec, PREC_LOGICAL_AND)

    @override
    def map_logical_or(self, expr: p.LogicalOr, /, enclosing_prec: int) -> str:
        return self.parenthesize_if_needed(
                self.join_rec(" || ", expr.children, PREC_LOGICAL_OR),
                enclosing_prec, PREC_LOGICAL_OR)

    @override
    def map_common_subexpression(
                self, expr: p.CommonSubexpression, /, enclosing_prec: int) -> str:
        try:
            cse_name = self.cse_to_name[expr.child]
        except KeyError:
            from pymbolic.mapper.stringifier import PREC_NONE
            cse_str = self.rec(expr.child, PREC_NONE)

            if expr.prefix is not None:
                def generate_cse_names() -> Iterator[str]:
                    yield f"{self.cse_prefix}_{expr.prefix}"
                    i = 2
                    while True:
                        yield f"{self.cse_prefix}_{expr.prefix}_{i}"
                        i += 1
            else:
                def generate_cse_names() -> Iterator[str]:
                    i = 0
                    while True:
                        yield f"{self.cse_prefix}{i}"
                        i += 1

            cse_name = None
            for cse_name in generate_cse_names():
                if cse_name not in self.cse_names:
                    break
            assert cse_name is not None

            self.cse_name_list.append((cse_name, cse_str))
            self.cse_to_name[expr.child] = cse_name
            self.cse_names.add(cse_name)

            assert len(self.cse_names) == len(self.cse_to_name)

        return cse_name

    @override
    def map_if(self, expr: p.If, /, enclosing_prec: int) -> str:
        from pymbolic.mapper.stringifier import PREC_NONE
        return self.format("(%s ? %s : %s)",
                self.rec(expr.condition, PREC_NONE),
                self.rec(expr.then, PREC_NONE),
                self.rec(expr.else_, PREC_NONE),
                )

    # }}}

# vim: foldmethod=marker
