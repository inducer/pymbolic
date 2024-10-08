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

import math

import pymbolic
from pymbolic.mapper.stringifier import PREC_NONE, StringifyMapper


class CompileMapper(StringifyMapper):
    def map_constant(self, expr, enclosing_prec):
        # work around numpy bug #1137 (locale-sensitive repr)
        # https://github.com/numpy/numpy/issues/1735
        try:
            import numpy
        except ImportError:
            pass
        else:
            if isinstance(expr, numpy.floating):
                expr = float(expr)
            elif isinstance(expr, numpy.complexfloating):
                expr = complex(expr)

        return repr(expr)

    def map_numpy_array(self, expr, enclosing_prec):
        def stringify_leading_dimension(ary):
            if len(ary.shape) == 1:
                def rec(expr):
                    return self.rec(expr, PREC_NONE)
            else:
                rec = stringify_leading_dimension

            return "[{}]".format(", ".join(rec(x) for x in ary))

        return "numpy.array({})".format(stringify_leading_dimension(expr))

    def map_foreign(self, expr, enclosing_prec):
        return StringifyMapper.map_foreign(self, expr, enclosing_prec)


class CompiledExpression:
    """This class encapsulates an expression compiled into Python bytecode
    for faster evaluation.

    Its instances (unlike plain lambdas) are pickleable.
    """

    def __init__(self, expression, variables=None):
        """
        :arg variables: The first arguments (as strings or
            :class:`pymbolic.primitives.Variable` instances) to be used for the
            compiled function.  All variables used by the expression and not
            present here are added in lexicographic order.
        """
        if variables is None:
            variables = []
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
        used_variables -= {pymbolic.var(key) for key in list(ctx.keys())}
        used_variables = list(used_variables)
        used_variables.sort()
        all_variables = self._Variables + used_variables

        expr_s = CompileMapper()(self._Expression, PREC_NONE)
        func_s = "lambda {}: {}".format(",".join(str(v) for v in all_variables),
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
