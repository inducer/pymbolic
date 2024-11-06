"""
.. autoclass:: DifferentiationMapper
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

import pymbolic
import pymbolic.mapper
import pymbolic.mapper.evaluator
import pymbolic.primitives as primitives


def map_math_functions_by_name(i, func, pars, allowed_nonsmoothness="none"):
    def make_f(name):
        return primitives.Lookup(primitives.Variable("math"), name)

    if func == make_f("sin") and len(pars) == 1:
        return make_f("cos")(*pars)
    elif func == make_f("cos") and len(pars) == 1:
        return -make_f("sin")(*pars)
    elif func == make_f("tan") and len(pars) == 1:
        return make_f("tan")(*pars)**2+1
    elif func == make_f("log") and len(pars) == 1:
        return primitives.quotient(1, pars[0])
    elif func == make_f("exp") and len(pars) == 1:
        return make_f("exp")(*pars)
    elif func == make_f("sinh") and len(pars) == 1:
        return make_f("cosh")(*pars)
    elif func == make_f("cosh") and len(pars) == 1:
        return make_f("sinh")(*pars)
    elif func == make_f("tanh") and len(pars) == 1:
        return 1-make_f("tanh")(*pars)**2
    elif func == make_f("expm1") and len(pars) == 1:
        return make_f("exp")(*pars)
    elif func == make_f("fabs") and len(pars) == 1:
        if allowed_nonsmoothness in ["continuous", "discontinuous"]:
            from pymbolic.functions import sign
            return sign(*pars)
        else:
            raise ValueError("fabs is not smooth"
                             ", pass allowed_nonsmoothness='continuous' "
                             "to return sign")
    elif func == make_f("copysign") and len(pars) == 2:
        if allowed_nonsmoothness == "discontinuous":
            return 0
        else:
            raise ValueError("sign is discontinuous"
                             ", pass allowed_nonsmoothness='discontinuous' "
                             "to return 0")
    else:
        raise RuntimeError("unrecognized function, cannot differentiate")


class DifferentiationMapper(pymbolic.mapper.Mapper,
        pymbolic.mapper.CSECachingMapperMixin):
    """Example usage:

    .. doctest::
        :options: +NORMALIZE_WHITESPACE

        >>> import pymbolic.primitives as p
        >>> x = p.Variable("x")
        >>> expr = x*(x+5)**3/(x-1)**2

        >>> from pymbolic import flatten
        >>> from pymbolic.mapper.differentiator import DifferentiationMapper as DM
        >>> print(flatten(DM(x)(expr)))
        (((x + 5)**3 + x*3*(x + 5)**2)*(x + -1)**2 + (-1)*2*(x + -1)*x*(x + 5)**3) / (x + -1)**2**2
    """  # noqa: E501

    def __init__(self, variable, func_map=map_math_functions_by_name,
                 allowed_nonsmoothness=None):
        """
        :arg variable: A :class:`pymbolic.primitives.Variable` instance
            by which to differentiate.
        :arg func_map: A function for computing derivatives of function
            calls, signature ``(arg_index, function_variable, parameters)``.
        :arg allowed_nonsmoothness: Whether to allow differentiation of
            functions which are not smooth or continuous.
            Pass ``"continuous"`` to allow nonsmooth but not discontinuous
            functions or ``"discontinuous"`` to allow both.
            Defaults to ``"none"``, in which case neither is allowed.

        .. versionchanged:: 2019.2

            Added *allowed_nonsmoothness*.
        """

        if allowed_nonsmoothness is None:
            allowed_nonsmoothness = "none"

        self.variable = variable
        self.function_map = func_map
        if allowed_nonsmoothness not in ["none", "continuous", "discontinuous"]:
            raise ValueError(f"allowed_nonsmoothness={allowed_nonsmoothness} "
                    "is not a valid option")
        self.allowed_nonsmoothness = allowed_nonsmoothness

    def rec_undiff(self, expr, *args):
        """This method exists for the benefit of subclasses that may need to
        process un-differentiated subexpressions.
        """
        return expr

    def map_constant(self, expr, *args):
        return 0

    def map_variable(self, expr, *args):
        if expr == self.variable:
            return 1
        else:
            return 0

    def map_call(self, expr, *args):
        return pymbolic.flattened_sum(
            self.function_map(
                i, expr.function, self.rec_undiff(expr.parameters, *args),
                allowed_nonsmoothness=self.allowed_nonsmoothness)
            * self.rec(par, *args)
            for i, par in enumerate(expr.parameters)
            )

    map_subscript = map_variable

    def map_sum(self, expr, *args):
        return pymbolic.flattened_sum(
                self.rec(child, *args) for child in expr.children)

    def map_product(self, expr, *args):
        return pymbolic.flattened_sum(
            pymbolic.flattened_product(
                [self.rec_undiff(ch, *args) for ch in expr.children[0:i]]
                + [self.rec(child, *args)]
                + [self.rec_undiff(ch, *args) for ch in expr.children[i+1:]]
                )
            for i, child in enumerate(expr.children))

    def map_quotient(self, expr, *args):
        f = expr.numerator
        g = expr.denominator
        df = self.rec(f, *args)
        dg = self.rec(g, *args)
        f = self.rec_undiff(f, *args)
        g = self.rec_undiff(g, *args)

        if (not df) and (not dg):
            return 0
        elif (not df):
            return -f*dg/g**2
        elif (not dg):
            return self.rec(f, *args)/g
        else:
            return (df*g-dg*f)/g**2

    def map_power(self, expr, *args):
        f = expr.base
        g = expr.exponent
        df = self.rec(f, *args)
        dg = self.rec(g, *args)
        f = self.rec_undiff(f, *args)
        g = self.rec_undiff(g, *args)

        log = pymbolic.var("log")

        if (not df) and (not dg):
            return 0
        elif (not df):
            return log(f) * f**g * dg
        elif (not dg):
            return g * f**(g-1) * df
        else:
            return log(f) * f**g * dg + \
                    g * f**(g-1) * df

    def map_numpy_array(self, expr, *args):
        import numpy
        result = numpy.empty(expr.shape, dtype=object)
        for i in numpy.ndindex(result.shape):
            result[i] = self.rec(expr[i], *args)
        return result

    def map_if(self, expr, *args):
        if self.allowed_nonsmoothness != "discontinuous":
            raise ValueError("cannot differentiate 'If' nodes unless "
                    "allowed_nonsmoothness is set to 'discontinuous'")

        return type(expr)(
                expr.condition,
                self.rec(expr.then, *args),
                self.rec(expr.else_, *args))

    def map_common_subexpression_uncached(self, expr, *args):
        return type(expr)(
                self.rec(expr.child, *args),
                expr.prefix,
                expr.scope)


def differentiate(expression,
                  variable,
                  func_mapper=map_math_functions_by_name,
                  allowed_nonsmoothness="none"):
    if not isinstance(variable, primitives.Variable | primitives.Subscript):
        variable = primitives.make_variable(variable)
    from pymbolic import flatten
    return flatten(DifferentiationMapper(
        variable, func_mapper, allowed_nonsmoothness=allowed_nonsmoothness
        )(expression))
