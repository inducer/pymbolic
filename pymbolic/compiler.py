from __future__ import division
from __future__ import absolute_import

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

import math
import pymbolic
from pymbolic.mapper.stringifier import (StringifyMapper, PREC_NONE,
        PREC_SUM, PREC_POWER)


def _constant_mapper(c):
    # work around numpy bug #1137 (locale-sensitive repr)
    # http://projects.scipy.org/numpy/ticket/1137
    try:
        import numpy
    except ImportError:
        pass
    else:
        if isinstance(c, numpy.floating):
            c = float(c)
        elif isinstance(c, numpy.complexfloating):
            c = complex(c)

    return repr(c)


class CompileMapper(StringifyMapper):
    def __init__(self):
        StringifyMapper.__init__(self,
                constant_mapper=_constant_mapper)

    def map_polynomial(self, expr, enclosing_prec):
        # Use Horner's scheme to evaluate the polynomial

        sbase = self(expr.base, PREC_POWER)

        def stringify_exp(exp):
            if exp == 0:
                return ""
            elif exp == 1:
                return "*%s" % sbase
            else:
                return "*%s**%s" % (sbase, exp)

        result = ""
        rev_data = expr.data[::-1]
        for i, (exp, coeff) in enumerate(rev_data):
            if i+1 < len(rev_data):
                next_exp = rev_data[i+1][0]
            else:
                next_exp = 0
            result = "(%s+%s)%s" % (result, self(coeff, PREC_SUM),
                    stringify_exp(exp-next_exp))

        if enclosing_prec > PREC_SUM and len(expr.data) > 1:
            return "(%s)" % result
        else:
            return result

    def map_numpy_array(self, expr, enclosing_prec):
        def stringify_leading_dimension(ary):
            if len(ary.shape) == 1:
                def rec(expr):
                    return self.rec(expr, PREC_NONE)
            else:
                rec = stringify_leading_dimension

            return "[%s]" % (", ".join(rec(x) for x in ary))

        return "numpy.array(%s)" % stringify_leading_dimension(expr)

    def map_foreign(self, expr, enclosing_prec):
        return StringifyMapper.map_foreign(self, expr, enclosing_prec)


class CompiledExpression(object):
    """This class encapsulates an expression compiled into Python bytecode
    for faster evaluation.

    Its instances (unlike plain lambdas) are pickleable.
    """

    def __init__(self, expression, variables=[]):
        """
        :arg variables: The first arguments (as strings or
            :class:`pymbolic.primitives.Variable` instances) to be used for the
            compiled function.  All variables used by the expression and not
            present here are added in alphabetical order.
        """
        self._compile(expression, variables)

    def _compile(self, expression, variables):
        import pymbolic.primitives as primi
        self._Expression = expression
        self._Variables = [primi.make_variable(v) for v in variables]
        ctx = self.context().copy()

        try:
            import numpy
        except ImportError:
            pass
        else:
            ctx["numpy"] = numpy

        from pymbolic.mapper.dependency import DependencyMapper
        used_variables = DependencyMapper(
                composite_leaves=False)(self._Expression)
        used_variables -= set(self._Variables)
        used_variables -= set(pymbolic.var(key) for key in list(ctx.keys()))
        used_variables = list(used_variables)
        used_variables.sort()
        all_variables = self._Variables + used_variables

        expr_s = CompileMapper()(self._Expression, PREC_NONE)
        func_s = "lambda %s: %s" % (",".join(str(v) for v in all_variables),
                expr_s)
        self._code = eval(func_s, ctx)

    def __getstate__(self):
        return self._Expression, self._Variables

    def __setstate__(self, state):
        self._compile(*state)

    def __call__(self, *args):
        return self._code(*args)

    def context(self):
        return {"math": math}


compile = CompiledExpression
