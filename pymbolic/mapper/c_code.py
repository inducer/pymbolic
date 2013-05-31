from __future__ import division

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

from pymbolic.mapper.stringifier import (
        SimplifyingSortingStringifyMapper, PREC_UNARY,
        PREC_LOGICAL_AND, PREC_LOGICAL_OR)


class CCodeMapper(SimplifyingSortingStringifyMapper):
    """Generate C code for expressions, while extracting
    :class:`pymbolic.primitives.CommonSubexpression` instances.

    As an example, define a fairly simple expression *expr*:

    .. doctest::

        >>> import pymbolic.primitives as p
        >>> x = p.Variable("x")
        >>> CSE = p.CommonSubexpression
        >>> u = CSE(3*x**2-5, "u")
        >>> expr = u/(u+3)*(u+5)
        >>> print expr
        CSE(3*x**2 + -5) / (CSE(3*x**2 + -5) + 3)*(CSE(3*x**2 + -5) + 5)

    Notice that if we were to directly generate code from this, the
    subexpression *u* would be evaluated multiple times.

    .. doctest::

        >>> from pymbolic.mapper.c_code import CCodeMapper as CCM
        >>> ccm = CCM()
        >>> result = ccm(expr)

        >>> for name, value in ccm.cse_name_list:
        ...     print "%s = %s;" % (name, value)
        ...
        _cse_u = 3 * x * x + -5;
        >>> print result
        _cse_u / (_cse_u + 3) * (_cse_u + 5)

    See :class:`pymbolic.mapper.stringifier.CSESplittingStringifyMapperMixin`
    for the ``cse_*`` attributes.
    """

    def __init__(self, constant_mapper=repr, reverse=True,
            cse_prefix="_cse", complex_constant_base_type="double",
            cse_name_list=[]):
        SimplifyingSortingStringifyMapper.__init__(self, constant_mapper, reverse)
        self.cse_prefix = cse_prefix

        self.cse_to_name = dict((cse, name) for name, cse in cse_name_list)
        self.cse_names = set(cse for name, cse in cse_name_list)
        self.cse_name_list = cse_name_list[:]

        self.complex_constant_base_type = complex_constant_base_type

    def copy(self, cse_name_list=None):
        if cse_name_list is None:
            cse_name_list = self.cse_name_list
        return CCodeMapper(self.constant_mapper, self.reverse,
                self.cse_prefix, self.complex_constant_base_type,
                cse_name_list)

    def copy_with_mapped_cses(self, cses_and_values):
        return self.copy(self.cse_name_list + cses_and_values)

    # {{{ mappings

    def map_product(self, expr, enclosing_prec):
        from pymbolic.mapper.stringifier import PREC_PRODUCT
        return self.parenthesize_if_needed(
                # Spaces prevent '**z' (times dereference z), which
                # is hard to read.

                self.join_rec(" * ", expr.children, PREC_PRODUCT),
                enclosing_prec, PREC_PRODUCT)

    def map_constant(self, x, enclosing_prec):
        if isinstance(x, complex):
            return "std::complex<%s>(%s, %s)" % (
                    self.complex_constant_base_type,
                    self.constant_mapper(x.real),
                    self.constant_mapper(x.imag))
        else:
            return SimplifyingSortingStringifyMapper.map_constant(
                    self, x, enclosing_prec)

    def map_call(self, expr, enclosing_prec):
        from pymbolic.primitives import Variable
        from pymbolic.mapper.stringifier import PREC_NONE, PREC_CALL
        if isinstance(expr.function, Variable):
            func = expr.function.name
        else:
            func = self.rec(expr.function, PREC_CALL)

        return self.format("%s(%s)",
                func, self.join_rec(", ", expr.parameters, PREC_NONE))

    def map_power(self, expr, enclosing_prec):
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

    def map_floor_div(self, expr, enclosing_prec):
        # Let's see how bad of an idea this is--sane people would only
        # apply this to integers, right?

        from pymbolic.mapper.stringifier import (
                PREC_PRODUCT, PREC_POWER)
        return self.format("(%s/%s)",
                    self.rec(expr.numerator, PREC_PRODUCT),
                    self.rec(expr.denominator, PREC_POWER))  # analogous to ^{-1}

    def map_logical_not(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                "!" + self.rec(expr.child, PREC_UNARY),
                enclosing_prec, PREC_UNARY)

    def map_logical_and(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.join_rec(" && ", expr.children, PREC_LOGICAL_AND),
                enclosing_prec, PREC_LOGICAL_AND)

    def map_logical_or(self, expr, enclosing_prec):
        return self.parenthesize_if_needed(
                self.join_rec(" || ", expr.children, PREC_LOGICAL_OR),
                enclosing_prec, PREC_LOGICAL_OR)

    def map_common_subexpression(self, expr, enclosing_prec):
        try:
            cse_name = self.cse_to_name[expr.child]
        except KeyError:
            from pymbolic.mapper.stringifier import PREC_NONE
            cse_str = self.rec(expr.child, PREC_NONE)

            if expr.prefix is not None:
                def generate_cse_names():
                    yield self.cse_prefix+"_"+expr.prefix
                    i = 2
                    while True:
                        yield self.cse_prefix+"_"+expr.prefix + "_%d" % i
                        i += 1
            else:
                def generate_cse_names():
                    i = 0
                    while True:
                        yield self.cse_prefix+str(i)
                        i += 1

            for cse_name in generate_cse_names():
                if cse_name not in self.cse_names:
                    break

            self.cse_name_list.append((cse_name, cse_str))
            self.cse_to_name[expr.child] = cse_name
            self.cse_names.add(cse_name)

            assert len(self.cse_names) == len(self.cse_to_name)

        return cse_name

    def map_if_positive(self, expr, enclosing_prec):
        from pymbolic.mapper.stringifier import PREC_NONE
        return self.format("(%s > 0 ? %s : %s)",
                self.rec(expr.criterion, PREC_NONE),
                self.rec(expr.then, PREC_NONE),
                self.rec(expr.else_, PREC_NONE),
                )

    def map_if(self, expr, enclosing_prec):
        from pymbolic.mapper.stringifier import PREC_NONE
        return self.format("(%s ? %s : %s)",
                self.rec(expr.condition, PREC_NONE),
                self.rec(expr.then, PREC_NONE),
                self.rec(expr.else_, PREC_NONE),
                )
    # }}}
